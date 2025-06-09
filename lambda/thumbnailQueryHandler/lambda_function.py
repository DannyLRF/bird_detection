import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("BirdTagsData")
s3 = boto3.client("s3")

def generate_presigned_url(s3_uri):
    if s3_uri and s3_uri.startswith("s3://"):
        bucket, key = s3_uri.replace("s3://", "").split("/", 1)
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=300  # 5 minutes
        )
    return None

def lambda_handler(event, context):
    try:
        if event.get("httpMethod", "").upper() != "POST":
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Only POST method is supported"})
            }

        body = json.loads(event.get("body", "{}"))
        input_thumb = body.get("thumbnail_url")

        if not input_thumb:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing thumbnail_url in request body"})
            }

        # Full scan — consider GSI for better performance if needed
        response = table.scan()
        for item in response.get("Items", []):
            if item.get("thumbnail_s3_url") == input_thumb:
                original_url = generate_presigned_url(item.get("original_s3_url"))

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "original_url": original_url,
                    })
                }

        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Thumbnail not found"})
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }
