import json
import boto3 # Requires install for local testing: pip install boto3
import os

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]  # Set this as an env variable in Lambda

def getSignedURL(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        file_name = body["fileName"]
        file_type = body["fileType"]  # Optional, used for headers

        # Generate pre-signed URL
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": file_name,
                "ContentType": file_type
            },
            ExpiresIn=180,
            HttpMethod="POST"  # URL expires in 3 minutes
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Adjust for security
                "Content-Type": "application/json"
            },
            "body": json.dumps({ "uploadUrl": url })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({ "error": str(e) })
        }
    
# def presignedTest():
#     request = {
#         "resource": "/upload",
#         "path": "/upload",
#         "httpMethod": "POST",
#         "headers": {
#             "Content-Type": "application/json"
#             },
#             "queryStringParameters": None,
#             "pathParameters": None,
#             "body": {"fileName": "photo.jpg", 
#                      "fileType": "jpeg"},
#             "isBase64Encoded": False
#             }
    
#     to_send = json.dumps(request)
    
#     url = getSignedURL(to_send, None)
#     print(url)

