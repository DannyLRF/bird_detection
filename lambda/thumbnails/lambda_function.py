import boto3
import os
from PIL import Image
from io import BytesIO

# Initialize the S3 client
s3 = boto3.client('s3')

def handler(event, context):
    print("Thumbnail Lambda triggered!")

    # Extract bucket name and object key from the S3 event
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    # Only handle image files
    if not key.lower().endswith(('.jpg', '.jpeg', '.png')):
        print(f"Unsupported file type: {key}")
        return {'statusCode': 400, 'body': 'Only image files are supported'}

    # Download the original image file from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    img_data = response['Body'].read()
    img = Image.open(BytesIO(img_data))

    # Generate a thumbnail with a maximum size of 256x256
    img.thumbnail((256, 256))

    # Save the thumbnail into an in-memory buffer
    buffer = BytesIO()
    img_format = img.format if img.format else 'JPEG'
    img.save(buffer, format=img_format)
    buffer.seek(0)

    # Define the output S3 key under the 'thumbnails/' folder
    filename = os.path.basename(key)
    thumb_key = f'thumbnails/{filename}'

    # Upload the thumbnail image to S3
    s3.put_object(
        Bucket=bucket,
        Key=thumb_key,
        Body=buffer,
        ContentType=f'image/{img_format.lower()}'
    )

    print(f"Thumbnail uploaded to: {thumb_key}")
    return {
        'statusCode': 200,
        'body': f'Thumbnail created at {thumb_key}'
    }