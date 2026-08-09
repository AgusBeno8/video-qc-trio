import sys
from pathlib import Path

# Add project root (/app) to Python's search path:
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Standard libraries:
import os
import json
import time
import urllib.parse
from pathlib import Path
import boto3

# video-qc-trio suite tier 1 tools and functions:
from AnalyzerMK1.AnalyzerMK1 import batch_analyze_videos
from ConforCheckMK1.ConforCheckerMK1 import batch_conformance_check
from RemuxerMK1.RemuxerMK1 import batch_remux


ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

sqs = boto3.client("sqs", endpoint_url=ENDPOINT, region_name=REGION)
s3 = boto3.client("s3", endpoint_url=ENDPOINT, region_name=REGION)
QUEUE_NAME = "video-qc-queue"

def process_video_job(bucket_name, object_key):
    #Downloads video from S3 to temp storage, executes selected tool, cleans up.
    local_temp_path = Path("/tmp") / Path(object_key).name

    try:
        print(f"[*] Downloading s3://{bucket_name}/{object_key} -> {local_temp_path}")
        s3.download_file(bucket_name, object_key, str(local_temp_path))

        # DETERMINE WHICH TOOL TO RUN. LINE 38.
        print(f"[>] Launching selected processing tool")
        batch_analyze_videos(local_temp_path)

        print(f"Execution successful.")

    except Exception as err:
        print(f"[-] Pipeline execution error on {object_key}: {err}")

    finally:
        # Guarantee temp file deletion to prevent filling up container storage
        if local_temp_path.exists():
            local_temp_path.unlink()
            print(f"[*] Cleaned up temp file: {local_temp_path}")

def get_queue_url():
    """Fetch the HTTP URL for polling."""
    response = sqs.get_queue_url(QueueName=QUEUE_NAME)
    return response["QueueUrl"]

def listen_for_videos():
    queue_url = get_queue_url()
    print(f"[*] Daemon active. Listening on SQS Queue: {QUEUE_NAME}...")

    while True:
        # 1. Long Poll SQS for messages
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,   # Get 1 video job at a time
            WaitTimeSeconds=20,      # Long polling: Waits up to 20s if queue is empty
            AttributeNames=["All"]
        )

        messages = response.get("Messages", [])

        if not messages:
            # No messages arrived during the 20s window, loop continues automatically
            continue

        for message in messages:
            receipt_handle = message["ReceiptHandle"]
            raw_body = message["Body"]

            # 2. Parse the JSON notification body
            try:
                body_json = json.loads(raw_body)
                
                # S3 event records are returned in a list inside 'Records'
                for record in body_json.get("Records", []):
                    bucket_name = record["s3"]["bucket"]["name"]
                    
                    # URL-decode the key (e.g., converts 'my+video.mp4' back to 'my video.mp4')
                    raw_key = record["s3"]["object"]["key"]
                    object_key = urllib.parse.unquote_plus(raw_key)

                    # ----------------------------------------------------
                    # VIDEO QUALITY CONTROL SCRIPT PROCESS CALLING:

                    # SQS message loop:
                    print(f"\n[+] NEW VIDEO DETECTED")
                    print(f"    - Bucket: {bucket_name}")
                    print(f"    - File Key: {object_key}")

                    # Call manager function that downloads, analyzes, and cleans up.
                    process_video_job(bucket_name, object_key)
                    # ----------------------------------------------------

            except Exception as e:
                print(f"[-] Error parsing SQS payload: {e}")

            # 3. Acknowledge & Delete the message from SQS
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            print("Message processed and deleted from queue.")

if __name__ == "__main__":
    listen_for_videos()