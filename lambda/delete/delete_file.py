import boto3
import os
import json
from urllib.parse import urlparse

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

audio_extensions = ["wav", "x-wav", "mp3"]

def delete_file(event, context):
    body = json.loads(event.get("body", "{}"))
    s3_urls = body.get("urls", [])

    deleted = []
    errors = []

    for url in s3_urls:
        try:
            file_name = extract_file_name(url)
            file_base, file_ext = file_name.rsplit(".", 1)
            print(file_name, file_base, file_ext)

            is_audio = file_ext.lower() in audio_extensions
            is_video = file_ext.lower() == "mp4"

            if is_audio:
                raw_key = f"audio/{file_name}"
                annotated_key = f"annotated/audio/{file_base}_predictions.json"

                s3.delete_object(Bucket=BUCKET_NAME, Key=raw_key)
                s3.delete_object(Bucket=BUCKET_NAME, Key=annotated_key)
                delete_from_dynamo(raw_key)

            elif is_video:
                raw_key = f"uploads/{file_name}"
                annotated_key = f"annotated/video/{file_base}.mp4"

                s3.delete_object(Bucket=BUCKET_NAME, Key=raw_key)
                s3.delete_object(Bucket=BUCKET_NAME, Key=annotated_key)
                delete_from_dynamo(raw_key)

            else:
                raw_key = f"uploads/{file_name}"
                annotated_key = f"annotated/images/{file_name}"
                thumbnail_key = f"thumbnails/{file_name}"

                s3.delete_object(Bucket=BUCKET_NAME, Key=raw_key)
                s3.delete_object(Bucket=BUCKET_NAME, Key=annotated_key)
                s3.delete_object(Bucket=BUCKET_NAME, Key=thumbnail_key)
                delete_from_dynamo(raw_key)

            deleted.append(file_name)

        except Exception as e:
            errors.append({"url": url, "error": str(e)})

    return {
        "statusCode": 200 if not errors else 207,
        "body": json.dumps({
            "deleted": deleted,
            "errors": errors
        })
    }

def extract_file_name(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

def delete_from_dynamo(raw_key):
    full_url = f"s3://{BUCKET_NAME}/{raw_key}"
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('original_s3_url').eq(full_url)
    )
    items = response.get('Items', [])
    for item in items:
        table.delete_item(Key={'file_id': item['file_id']})
