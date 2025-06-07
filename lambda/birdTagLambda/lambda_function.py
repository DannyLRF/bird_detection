import json
import boto3
from utils import run_inference, draw_detections, process_video
from PIL import Image
import io
import os
import uuid
from collections import Counter

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
        input_path = "/tmp/input.jpg"
        annotated_path = "/tmp/annotated.jpg"

        image_obj = s3.get_object(Bucket=bucket, Key=key)
        image_bytes = image_obj['Body'].read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.save(input_path)

        detections = run_inference(input_path)
        draw_detections(input_path, detections, annotated_path)

        output_key = "annotated/images/" + os.path.basename(key)
        with open(annotated_path, "rb") as f:
            s3.upload_fileobj(f, "team99-uploaded-files", output_key)

    elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
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

    print("Inference complete...")

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'file_id': file_id,
        'file_type': 'video' if ext in [".mp4", ".avi", ".mov", ".mkv"] else 'image',
        'original_s3_url': f"s3://{bucket}/{key}",
        'annotated_s3_url': annotated_url,
        "detected_birds": bird_summary
    })

    print("Done writing to DynamoDB, about to return...")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Inference complete",
            "detected_birds": bird_summary,
            "annotated_output": annotated_url
        })
    }

    print("This should not run")



