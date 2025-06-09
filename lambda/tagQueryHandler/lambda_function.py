import json
import base64
import tempfile
import boto3
from decimal import Decimal
from utils import run_inference, process_video
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("BirdTagsData")
s3 = boto3.client("s3")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

def generate_presigned_url(s3_uri):
    if not s3_uri or not s3_uri.startswith("s3://"):
        return None
    try:
        bucket, key = s3_uri.replace("s3://", "").split("/", 1)
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=300
        )
    except Exception as e:
        logger.error(f"Presigned URL error for {s3_uri}: {e}")
        return None

def lambda_handler(event, context):
    try:
        # Decode base64 file
        body = json.loads(event.get("body", "{}"))
        file_b64 = body.get("file_base64")
        file_type = body.get("file_type", "image")  # "image" or "video"

        if not file_b64:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'file_base64'"})
            }

        file_bytes = base64.b64decode(file_b64)
        logger.info("File decoded successfully, length: %d bytes", len(file_bytes))

        tags = []

        if file_type == "video":
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                tags = process_video(tmp.name)
        else:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                results = run_inference(tmp.name)  # returns list of dicts
                tags = [r["label"].lower() for r in results if "label" in r]

        logger.info("Inference completed, detected tags: %s", tags)

        if not tags:
            return {
                "statusCode": 200,
                "body": json.dumps({"matched_files": [], "count": 0})
            }

        # Query DynamoDB for matching records
        response = table.scan()
        matched_results = []

        for item in response.get("Items", []):
            detected = item.get("detected_birds", [])
            detected_labels = {d.get("label", "").lower() for d in detected if "label" in d}

            if all(tag in detected_labels for tag in tags):
                result = {
                    "filename": item.get("filename"),
                    "thumbnail_url": generate_presigned_url(item.get("thumbnail_s3_url")),
                    "annotated_url": generate_presigned_url(item.get("annotated_s3_url")),
                    "original_url": generate_presigned_url(item.get("original_s3_url")),
                    "tags": [d.get("label") for d in detected]
                }
                matched_results.append(result)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "matched_files": matched_results,
                "count": len(matched_results)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.exception("Unhandled error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }
