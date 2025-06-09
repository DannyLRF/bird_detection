import json
import boto3
import os

sns = boto3.client('sns')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        bird_tags = body.get("birdTag")

        if not email or not bird_tags:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'email' or 'birdTag'"})
            }

        # Subscribe the email address
        subscribe_response = sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )

        subscription_arn = subscribe_response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}")

        # Set the filter policy
        filter_policy = {
            "birdTag": bird_tags
        }

        sns.set_subscription_attributes(
            SubscriptionArn=subscription_arn,
            AttributeName='FilterPolicy',
            AttributeValue=json.dumps(filter_policy)
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Subscription request sent. Please confirm via the email sent to your email.",
                "subscription_arn": subscription_arn
            })
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
