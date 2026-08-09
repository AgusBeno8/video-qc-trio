import os
import json
import boto3

# Connect to LocalStack via environment variables
ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

s3_client = boto3.client("s3", endpoint_url=ENDPOINT, region_name=REGION)
sqs_client = boto3.client("sqs", endpoint_url=ENDPOINT, region_name=REGION)

BUCKET_NAME = "video-incoming"
QUEUE_NAME = "video-qc-queue"

def init_infrastructure():
    # 1. Create S3 Bucket
    print(f"Creating S3 Bucket: {BUCKET_NAME}...")
    s3_client.create_bucket(Bucket=BUCKET_NAME)

    # 2. Create SQS Queue
    print(f"Creating SQS Queue: {QUEUE_NAME}...")
    queue_res = sqs_client.create_queue(QueueName=QUEUE_NAME)
    queue_url = queue_res["QueueUrl"]

    # Retrieve SQS Queue ARN (Amazon Resource Name) for S3 binding
    queue_attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"]
    )
    queue_arn = queue_attrs["Attributes"]["QueueArn"]

    # 3. Link S3 Object Creation Events -> SQS Queue
    notification_config = {
        "QueueConfigurations": [
            {
                "QueueArn": queue_arn,
                "Events": ["s3:ObjectCreated:*"]
            }
        ]
    }
    
    s3_client.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration=notification_config
    )

    print("Successfully initialized S3 Bucket, SQS Queue, and Event Notification Trigger!")

if __name__ == "__main__":
    init_infrastructure()