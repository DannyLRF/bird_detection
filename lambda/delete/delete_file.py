import boto3
import os
import json

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']

def delete_file(event, context):
    body = json.loads(event.get("body", "{}"))
    file_name = body['fileName']
    folder_path = "images"
    key = f"{folder_path}/{file_name}"

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        return {
            "statusCode": 200,
            "body": f"{file_name} deleted."
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
