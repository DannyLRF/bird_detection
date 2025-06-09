import boto3
import os

sns = boto3.client('sns')
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            new_image = record['dynamodb']['NewImage']

            file_id = new_image['file_id']['S']
            file_type = new_image['file_type']['S']
            s3_url = new_image['original_s3_url']['S']
            
            # Extract detected bird labels
            detected_birds_raw = new_image.get('detected_birds', {}).get('L', [])
            bird_labels = []
            for bird in detected_birds_raw:
                label = bird['M']['label']['S']
                bird_labels.append(label)

            for tag in bird_labels:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="New Bird Image Available",
                    Message=f"An image containing {tag} is available: {s3_url}",
                    MessageAttributes={
                        "birdTag": {
                            "DataType": "String",
                            "StringValue": tag
                        }
                    }
                )

            return {"statusCode": 200}
