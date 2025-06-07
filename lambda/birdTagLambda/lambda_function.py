import json
import boto3
from utils import run_inference, draw_detections, process_video
from PIL import Image
import io
import os
import uuid
from collections import Counter
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = "BirdTagsData"

def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    file_id = str(uuid.uuid4())

    _, ext = os.path.splitext(key.lower())

    if ext in [".jpg", ".jpeg", ".png"]:
        logger.info("Processing image file...")
        thumbnail_key = key
        logger.info(f"Thumbnail key: {thumbnail_key}")
        filename = os.path.basename(thumbnail_key)  # "bird.jpg"
        logger.info(f"Filename: {filename}")
        original_key = "uploads/" + filename  # "uploads/bird.jpg"
        logger.info(f"Original key: {original_key}")
        annotated_key = "annotated/images/" + filename
        logger.info(f"Annotated key: {annotated_key}")

        input_path = "/tmp/input.jpg"
        annotated_path = "/tmp/annotated.jpg"

        try:
            # Download original image for inference
            logger.info(f"Fetching original image from S3 at {original_key}")
            image_obj = s3.get_object(Bucket=bucket, Key=original_key)
            image_bytes = image_obj['Body'].read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image.save(input_path)
            logger.info(f"Original image fetched successfully from {original_key}")
            
        except Exception as e:
            logger.info(f"Failed to fetch original image at {original_key}")
            return {"statusCode": 404, "body": "Original image not found."}

        # Inference and annotation
        detections = run_inference(input_path)
        draw_detections(input_path, detections, annotated_path)

        with open(annotated_path, "rb") as f:
            s3.upload_fileobj(f, "team99-uploaded-files", annotated_key)

        output_key = annotated_key
        original_url = f"s3://{bucket}/{original_key}"
        thumbnail_url = f"s3://{bucket}/{thumbnail_key}"

    elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
        logger.info("Processing video file...")
        input_path = "/tmp/input" + ext
        annotated_path = "/tmp/annotated" + ext

        s3.download_file(bucket, key, input_path)
        detections = process_video(input_path, annotated_path)

        output_key = "annotated/videos/" + os.path.basename(key)
        with open(annotated_path, "rb") as f:
            s3.upload_fileobj(f, "team99-uploaded-files", output_key)

    else:
        return {"statusCode": 400, "body": "Unsupported file type"}

    label_counts = Counter(d['label'] for d in detections)
    bird_summary = [{"label": label, "count": count} for label, count in label_counts.items()]
    annotated_url = f"s3://{bucket}/{output_key}"

    logger.info("Inference complete...")

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'file_id': file_id,
        'file_type': 'video' if ext in [".mp4", ".avi", ".mov", ".mkv"] else 'image',
        'original_s3_url': original_url if ext in [".jpg", ".jpeg", ".png"] else f"s3://{bucket}/{key}",
        'thumbnail_s3_url': thumbnail_url if ext in [".jpg", ".jpeg", ".png"] else None,
        'annotated_s3_url': f"s3://{bucket}/{output_key}" if ext in [".mp4", ".avi", ".mov", ".mkv"] else annotated_url,
        "detected_birds": bird_summary
    })

    logger.info("Done writing to DynamoDB, about to return...")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Inference complete",
            "detected_birds": bird_summary,
            "annotated_output": annotated_url
        })
    }
