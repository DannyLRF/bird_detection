import os
import sys

# 在导入其他库之前设置环境变量
os.environ['NUMBA_CACHE_DIR'] = '/tmp'
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_DIR'] = '/tmp'

import json
import boto3
import base64
import tempfile
import numpy as np
import librosa
from pathlib import Path
import logging
import tensorflow as tf
from urllib.parse import unquote_plus

# 设置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AudioProcessor:
    """轻量级音频处理工具"""
    
    @staticmethod
    def load_audio(file_path, target_sr=48000):
        """加载音频文件"""
        try:
            # 使用librosa加载
            audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
            return audio.astype(np.float32), target_sr
            
        except Exception as e:
            logger.error(f"音频加载失败: {e}")
            raise
    
    @staticmethod
    def segment_audio(audio, sr, segment_length=3.0):
        """将音频分割为固定长度的片段"""
        segment_samples = int(segment_length * sr)
        segments = []
        
        for i in range(0, len(audio), segment_samples):
            segment = audio[i:i + segment_samples]
            
            if len(segment) == segment_samples:
                segments.append(segment)
            elif len(segment) > segment_samples * 0.5:  # 至少1.5秒
                # 用零填充到完整长度
                padded_segment = np.pad(segment, (0, segment_samples - len(segment)), 'constant')
                segments.append(padded_segment)
        
        return np.array(segments)

class BirdNETPredictor:
    def __init__(self):
        self.model_path = '/tmp/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite'
        self.labels_path = '/tmp/BirdNET_GLOBAL_6K_V2.4_Labels.txt'
        # 修改模型和标签文件所在的S3桶和键
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
        """从S3下载模型和标签文件"""
        if self._model_loaded:
            return
            
        s3 = boto3.client('s3')
        
        try:
            # 下载模型文件
            if not os.path.exists(self.model_path):
                logger.info("下载模型文件...")
                s3.download_file(self.model_s3_bucket, self.model_s3_key, self.model_path)
                logger.info(f"模型文件下载完成: {os.path.getsize(self.model_path)} bytes")
            
            # 下载标签文件
            if not os.path.exists(self.labels_path):
                logger.info("下载标签文件...")
                s3.download_file(self.labels_s3_bucket, self.labels_s3_key, self.labels_path)
                logger.info(f"标签文件下载完成: {os.path.getsize(self.labels_path)} bytes")
                
            self._model_loaded = True
                
        except Exception as e:
            logger.error(f"从S3下载文件失败: {e}")
            raise
    
    def _load_labels(self):
        """加载鸟类标签"""
        try:
            with open(self.labels_path, 'r', encoding='utf-8') as f:
                self.labels = [line.strip() for line in f.readlines()]
            logger.info(f"加载了 {len(self.labels)} 个标签")
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
            raise
    
    def _load_model(self):
        """加载TensorFlow Lite模型"""
        try:
            self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            logger.info("模型加载成功")
            logger.info(f"输入形状: {self.input_details[0]['shape']}")
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise
    
    def _preprocess_audio_from_s3(self, bucket_name: str, object_key: str):
        """从S3下载并预处理音频文件"""
        s3 = boto3.client('s3')
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 从S3下载音频文件
            logger.info(f"从S3下载音频文件: s3://{bucket_name}/{object_key}")
            s3.download_file(bucket_name, object_key, tmp_path)
            
            # 使用音频处理器加载和分割
            audio, sr = AudioProcessor.load_audio(tmp_path, self.sample_rate)
            logger.info(f"音频加载完成: 长度={len(audio)}, 采样率={sr}")
            
            segments = AudioProcessor.segment_audio(audio, sr, self.segment_length)
            logger.info(f"分割为 {len(segments)} 个片段")
            
            return segments, object_key
            
        except Exception as e:
            logger.error(f"从S3处理音频失败: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _preprocess_audio_from_base64(self, audio_data: bytes):
        """从base64数据预处理音频"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            audio, sr = AudioProcessor.load_audio(tmp_path, self.sample_rate)
            logger.info(f"音频加载完成: 长度={len(audio)}, 采样率={sr}")
            
            segments = AudioProcessor.segment_audio(audio, sr, self.segment_length)
            logger.info(f"分割为 {len(segments)} 个片段")
            
            return segments, "uploaded_audio"
            
        except Exception as e:
            logger.error(f"音频预处理失败: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def predict(self, audio_segments, confidence_threshold=0.1):
        """预测鸟类"""
        if self.interpreter is None:
            self._download_files_from_s3()
            self._load_labels()
            self._load_model()
        
        results = []
        
        for i, segment in enumerate(audio_segments):
            try:
                # 预处理音频段
                input_data = np.expand_dims(segment, axis=0).astype(np.float32)
                
                # 运行推理
                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                self.interpreter.invoke()
                
                # 获取预测结果
                predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                
                # 获取top 5预测
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
                logger.error(f"预测片段 {i} 时出错: {e}")
                continue
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results

    def _save_predictions_to_s3(self, predictions_data: dict, original_object_key: str):
        """将预测结果保存到S3"""
        s3 = boto3.client('s3')
        output_bucket_name = 'team99-uploaded-files'
        
        # 构建输出文件键
        # 移除原文件名的扩展名，并添加.json
        base_filename = Path(original_object_key).stem
        output_s3_key = f"annotated/audio/{base_filename}_predictions.json"

        try:
            logger.info(f"将预测结果保存到S3: s3://{output_bucket_name}/{output_s3_key}")
            s3.put_object(
                Bucket=output_bucket_name,
                Key=output_s3_key,
                Body=json.dumps(predictions_data, ensure_ascii=False),
                ContentType='application/json'
            )
            logger.info("预测结果保存成功。")
            return output_s3_key
        except Exception as e:
            logger.error(f"保存预测结果到S3失败: {e}")
            raise

# 全局变量，避免冷启动重复初始化
predictor = None

def lambda_handler(event, context):
    global predictor
    
    try:
        # 初始化预测器
        if predictor is None:
            predictor = BirdNETPredictor()
        
        logger.info(f"收到事件: {json.dumps(event)}")
        
        # 处理S3事件
        if 'Records' in event:
            results_all = []
            
            for record in event['Records']:
                if 's3' in record:
                    s3_info = record['s3']
                    bucket_name = s3_info['bucket']['name']
                    object_key = unquote_plus(s3_info['object']['key'])
                    
                    # 确保object_key是相对路径，不包含桶名
                    # 如果S3事件的bucket_name包含了多余的部分（如team99-uploaded-files/audio）
                    # 那么需要修正object_key，使其只包含文件路径
                    if bucket_name.endswith('/audio'):
                        # 假设实际的桶名是team99-uploaded-files
                        actual_bucket_name = bucket_name[:-len('/audio')]
                        # 并且object_key可能不包含audio/前缀，需要补上
                        if not object_key.startswith('audio/'):
                             object_key = f"audio/{object_key}"
                    else:
                        actual_bucket_name = bucket_name # 正常的桶名
                        
                    logger.info(f"处理S3对象: s3://{actual_bucket_name}/{object_key}")
                    
                    # 从S3处理音频
                    audio_segments, filename = predictor._preprocess_audio_from_s3(actual_bucket_name, object_key)
                    
                    # 运行预测
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

                    # 将预测结果保存到S3
                    try:
                        output_s3_path = predictor._save_predictions_to_s3(result, object_key)
                        result['output_s3_path'] = output_s3_path
                    except Exception as e:
                        logger.error(f"无法保存预测结果到S3: {e}")
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
        
        # 处理直接的API调用（包含audio_data的情况）
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
        
        # 解码音频数据
        try:
            audio_data = base64.b64decode(audio_base64)
            logger.info(f"音频数据大小: {len(audio_data)} bytes")
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid base64 audio data: {str(e)}'})
            }
        
        # 预处理音频
        audio_segments, filename = predictor._preprocess_audio_from_base64(audio_data)
        
        # 运行预测
        predictions = predictor.predict(audio_segments, confidence_threshold)
        
        # 格式化结果
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

        # 对于直接上传的音频，我们也尝试保存结果到S3，需要一个文件名来构建S3键
        # 假设直接上传的文件名是'uploaded_audio.wav'或者可以通过其他方式获取
        # 这里为了演示，我们假设它有一个虚拟的文件名
        try:
            # 对于直接上传的音频，我们无法直接获取原始的object_key
            # 这里可以生成一个基于当前时间戳的唯一文件名，或者在请求体中要求提供一个文件名
            # 为了简化，我们假设它是一个固定的名称，或者从事件中获取（如果存在）
            original_file_identifier = body.get('filename', 'uploaded_audio.wav') # 假设API调用可以提供文件名
            output_s3_path = predictor._save_predictions_to_s3(result, original_file_identifier)
            result['output_s3_path'] = output_s3_path
        except Exception as e:
            logger.error(f"无法保存直接上传的音频的预测结果到S3: {e}")
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
        logger.error(f"处理请求时出错: {str(e)}")
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