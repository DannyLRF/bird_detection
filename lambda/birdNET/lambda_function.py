import os
import sys

# Set environment variables before importing other libraries
os.environ['NUMBA_CACHE_DIR'] = '/tmp'
# os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_DIR'] = '/tmp'

import json
import boto3
import base64
import tempfile
import numpy as np
from pathlib import Path
import logging
import tensorflow as tf
import uuid
import re
import soundfile as sf
from collections import Counter
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote_plus
from scipy.signal import resample

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = "BirdTagsData"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

class AudioProcessor:
    @staticmethod
    def load_audio(file_path, target_sr=48000):
        """Load audio using soundfile, resample using scipy"""
        try:
            audio, sr = sf.read(file_path)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)  # convert to mono
            
            if sr != target_sr:
                duration = len(audio) / sr
                target_length = int(duration * target_sr)
                audio = resample(audio, target_length)
            
            return audio.astype(np.float32), target_sr
        except Exception as e:
            logger.error(f"Audio loading failed: {e}")
            raise
    
    @staticmethod
    def segment_audio(audio, sr, segment_length=3.0):
        """Split audio into fixed-length segments"""
        segment_samples = int(segment_length * sr)
        segments = []
        
        for i in range(0, len(audio), segment_samples):
            segment = audio[i:i + segment_samples]
            
            if len(segment) == segment_samples:
                segments.append(segment)
            elif len(segment) > segment_samples * 0.5:  # At least 1.5 seconds
                # Pad with zeros to full length
                padded_segment = np.pad(segment, (0, segment_samples - len(segment)), 'constant')
                segments.append(padded_segment)
        
        return np.array(segments)
    
SIMPLIFIED_LABELS = ["Crow", "Kingfisher", "Myna", "Owl", "Peacock", "Pigeon", "Sparrow"]
    
def simplify_species_name(full_name):
    common_name = full_name.split('_')[-1].strip().lower()
    for label in SIMPLIFIED_LABELS:
        if re.search(rf"\b{label.lower()}\b", common_name):
            return label
    return None

def store_predictions_to_dynamodb_audio(prediction_result):
    logger.info("Storing audio predictions to DynamoDB...")
    file_key = prediction_result["file"]
    bucket = prediction_result["bucket"]
    filename = Path(file_key).name
    predictions = prediction_result["predictions"]
    
    detected_labels = set()

    for p in predictions:
        simplified = simplify_species_name(p["species"])
        if simplified:
            detected_labels.add(simplified)

    if not detected_labels:
        logger.info("No relevant bird species detected, skipping DynamoDB storage.")
        return
    
    file_id = str(uuid.uuid4())
    s3_base = f"s3://{bucket}"
    
    item = {
        "file_id": file_id,
        "annotated_s3_url": f"{s3_base}/annotated/audio/{Path(filename).stem}_predictions.json",
        "detected_birds": [
            {"label": label, "count": 1} for label in detected_labels
        ],
        "file_type": "audio",
        "original_s3_url": f"{s3_base}/{file_key}",
        "thumbnail_s3_url": None
    }

    logger.info(f"Storing item in DynamoDB: {item}")
    table.put_item(Item=item)
    logger.info(f"Stored audio prediction for {filename} in DynamoDB.")

class BirdNETPredictor:
    def __init__(self):
        self.model_path = '/tmp/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite'
        self.labels_path = '/tmp/BirdNET_GLOBAL_6K_V2.4_Labels.txt'
        # Modify the S3 bucket and key for model and label files
        self.model_s3_bucket = 'team99-bird-detection-models'
        self.model_s3_key = 'birdNET/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite'
        self.labels_s3_bucket = 'team99-bird-detection-models'
        self.labels_s3_key = 'birdNET/BirdNET_GLOBAL_6K_V2.4_Labels.txt'

        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.sample_rate = 48000
        self.segment_length = 3.0
        self._model_loaded = False
        
    def _download_files_from_s3(self):
        """Download model and label files from S3"""
        if self._model_loaded:
            return
            
        s3 = boto3.client('s3')
        
        try:
            # Download model file
            if not os.path.exists(self.model_path):
                logger.info("Downloading model file...")
                s3.download_file(self.model_s3_bucket, self.model_s3_key, self.model_path)
                logger.info(f"Model file download completed: {os.path.getsize(self.model_path)} bytes")
            
            # Download label file
            if not os.path.exists(self.labels_path):
                logger.info("Downloading label file...")
                s3.download_file(self.labels_s3_bucket, self.labels_s3_key, self.labels_path)
                logger.info(f"Label file download completed: {os.path.getsize(self.labels_path)} bytes")
                
            self._model_loaded = True
                
        except Exception as e:
            logger.error(f"Failed to download files from S3: {e}")
            raise
    
    def _load_labels(self):
        """Load bird species labels"""
        try:
            with open(self.labels_path, 'r', encoding='utf-8') as f:
                self.labels = [line.strip() for line in f.readlines()]
            logger.info(f"Loaded {len(self.labels)} labels")
        except Exception as e:
            logger.error(f"Failed to load labels: {e}")
            raise
    
    def _load_model(self):
        """Load TensorFlow Lite model"""
        try:
            self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            logger.info("Model loaded successfully")
            logger.info(f"Input shape: {self.input_details[0]['shape']}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _preprocess_audio_from_s3(self, bucket_name: str, object_key: str):
        """Download and preprocess audio file from S3"""
        s3 = boto3.client('s3')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Download audio file from S3
            logger.info(f"Downloading audio file from S3: s3://{bucket_name}/{object_key}")
            s3.download_file(bucket_name, object_key, tmp_path)
            
            # Load and segment using audio processor
            audio, sr = AudioProcessor.load_audio(tmp_path, self.sample_rate)
            logger.info(f"Audio loaded successfully: length={len(audio)}, sample_rate={sr}")
            
            segments = AudioProcessor.segment_audio(audio, sr, self.segment_length)
            logger.info(f"Split into {len(segments)} segments")
            
            return segments, object_key
            
        except Exception as e:
            logger.error(f"Failed to process audio from S3: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _preprocess_audio_from_base64(self, audio_data: bytes):
        """Preprocess audio from base64 data"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            audio, sr = AudioProcessor.load_audio(tmp_path, self.sample_rate)
            logger.info(f"Audio loaded successfully: length={len(audio)}, sample_rate={sr}")
            
            segments = AudioProcessor.segment_audio(audio, sr, self.segment_length)
            logger.info(f"Split into {len(segments)} segments")
            
            return segments, "uploaded_audio"
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def predict(self, audio_segments, confidence_threshold=0.1):
        """Predict bird species"""
        if self.interpreter is None:
            self._download_files_from_s3()
            self._load_labels()
            self._load_model()
        
        results = []
        
        for i, segment in enumerate(audio_segments):
            try:
                # Preprocess audio segment
                input_data = np.expand_dims(segment, axis=0).astype(np.float32)
                
                # Run inference
                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                self.interpreter.invoke()
                
                # Get prediction results
                predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                
                # Get top 5 predictions
                top_indices = np.argsort(predictions)[-5:][::-1]
                
                for idx in top_indices:
                    confidence = float(predictions[idx])
                    if confidence > confidence_threshold:
                        timestamp = i * self.segment_length
                        species_name = self.labels[idx] if idx < len(self.labels) else f"Unknown_{idx}"
                        
                        results.append({
                            'species': species_name,
                            'confidence': confidence,
                            'timestamp': timestamp,
                            'segment': i
                        })
                        
            except Exception as e:
                logger.error(f"Error predicting segment {i}: {e}")
                continue
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results

    def _save_predictions_to_s3(self, predictions_data: dict, original_object_key: str):
        """Save prediction results to S3"""
        s3 = boto3.client('s3')
        output_bucket_name = 'team99-uploaded-files'
        
        # Build output file key
        # Remove original filename extension and add .json
        base_filename = Path(original_object_key).stem
        output_s3_key = f"annotated/audio/{base_filename}_predictions.json"

        try:
            logger.info(f"Saving prediction results to S3: s3://{output_bucket_name}/{output_s3_key}")
            s3.put_object(
                Bucket=output_bucket_name,
                Key=output_s3_key,
                Body=json.dumps(predictions_data, ensure_ascii=False),
                ContentType='application/json'
            )
            logger.info("Prediction results saved successfully.")
            return output_s3_key
        except Exception as e:
            logger.error(f"Failed to save prediction results to S3: {e}")
            raise

# Global variable to avoid cold start reinitialization
predictor = None

def lambda_handler(event, context):
    global predictor
    
    try:
        # Initialize predictor
        if predictor is None:
            predictor = BirdNETPredictor()
        
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle S3 events
        if 'Records' in event:
            results_all = []
            
            for record in event['Records']:
                if 's3' in record:
                    s3_info = record['s3']
                    bucket_name = s3_info['bucket']['name']
                    object_key = unquote_plus(s3_info['object']['key'])
                    
                    # Ensure object_key is a relative path, not including bucket name
                    # If S3 event bucket_name contains extra parts (like team99-uploaded-files/audio)
                    # then we need to correct object_key to include only the file path
                    if bucket_name.endswith('/audio'):
                        # Assume actual bucket name is team99-uploaded-files
                        actual_bucket_name = bucket_name[:-len('/audio')]
                        # And object_key might not include audio/ prefix, need to add it
                        if not object_key.startswith('audio/'):
                             object_key = f"audio/{object_key}"
                    else:
                        actual_bucket_name = bucket_name # Normal bucket name
                        
                    logger.info(f"Processing S3 object: s3://{actual_bucket_name}/{object_key}")
                    
                    # Process audio from S3
                    audio_segments, filename = predictor._preprocess_audio_from_s3(actual_bucket_name, object_key)
                    
                    # Run prediction
                    confidence_threshold = 0.1
                    predictions = predictor.predict(audio_segments, confidence_threshold)
                    
                    result = {
                        'file': filename,
                        'bucket': actual_bucket_name,
                        'total_segments': len(audio_segments),
                        'total_detections': len(predictions),
                        'predictions': predictions[:20]
                    }
                    
                    results_all.append(result)

                    # Save prediction results to S3
                    try:
                        output_s3_path = predictor._save_predictions_to_s3(result, object_key)
                        store_predictions_to_dynamodb_audio(result)
                        result['output_s3_path'] = output_s3_path
                    except Exception as e:
                        logger.error(f"Unable to save prediction results to S3: {e}")
                        result['s3_save_error'] = str(e)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'processing_type': 's3_event',
                    'files_processed': len(results_all),
                    'results': results_all
                }, ensure_ascii=False)
            }
        
        # Handle direct API calls (cases with audio_data)
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event
        
        audio_base64 = body.get('audio_data')
        confidence_threshold = body.get('confidence_threshold', 0.1)
        
        if not audio_base64:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No audio data provided or S3 event format'})
            }
        
        # Decode audio data
        try:
            audio_data = base64.b64decode(audio_base64)
            logger.info(f"Audio data size: {len(audio_data)} bytes")
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid base64 audio data: {str(e)}'})
            }
        
        # Preprocess audio
        audio_segments, filename = predictor._preprocess_audio_from_base64(audio_data)
        
        # Run prediction
        predictions = predictor.predict(audio_segments, confidence_threshold)
        
        # Format results
        result = {
            'success': True,
            'processing_type': 'direct_upload',
            'total_segments': len(audio_segments),
            'total_detections': len(predictions),
            'predictions': predictions[:20],
            'processing_info': {
                'segments_processed': len(audio_segments),
                'confidence_threshold': confidence_threshold
            }
        }

        # For directly uploaded audio, we also try to save results to S3, need a filename to build S3 key
        # Assume directly uploaded files are named 'uploaded_audio.wav' or can be obtained through other means
        # Here for demonstration, we assume it has a virtual filename
        try:
            # For directly uploaded audio, we can't directly get the original object_key
            # Here we can generate a unique filename based on current timestamp, or require a filename in the request body
            # For simplicity, we assume it's a fixed name, or get it from event (if exists)
            original_file_identifier = body.get('filename', 'uploaded_audio.wav') # Assume API call can provide filename
            output_s3_path = predictor._save_predictions_to_s3(result, original_file_identifier)
            store_predictions_to_dynamodb_audio(result)
            result['output_s3_path'] = output_s3_path
        except Exception as e:
            logger.error(f"Unable to save prediction results for directly uploaded audio to S3: {e}")
            result['s3_save_error'] = str(e)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }