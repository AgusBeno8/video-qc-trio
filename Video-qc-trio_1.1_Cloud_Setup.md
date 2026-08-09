#Cloud [[Cloud Workflows]]

This is a comprehensive roadmap of the setup process to replicate the video-qc-trio repository's cloud enviroment.

### 0) Overview of contents

Within the video-qc-trio 1.1 folder (Cloud mockup version) you will see the next files and folders in order:

Previous original folders and files:
* .github (This is the CI checking utilizing a yml with github actions)
* AnalyzerMK1 folder (The folder containing the "Analyzed" Output and Input folder of the Analyzer, whose input is mostly non used in the cloud version due to the automatic intake with the S3-daemon processing. And it's README file, besides an example of a JSON report it outputs.)
* ConforCheckMK1 folder (The folder containing the "Compliance_report" Output and Input folder of the Conformance Checker, whose input is mostly non used in the cloud version due to the automatic intake with the S3-daemon processing. And it's README file, besides an example of a JSON compliance report it outputs.)
* RemuxerMK1 folder (The folder containing the "Remuxed" output folder and Input folder of the Remuxer, whose input is mostly non used in the cloud version due to the automatic intake with the S3-daemon processing. And it's README file, besides an example of a JSON report it outputs.)
* requirements.txt (Updated by including boto3, the rest of libraries that aren't av come with python 3.11+ prepackaged)
* main README.txt file (Overview of the original programs)
* License (MIT)

New additions:
* bucket_daemon_setup folder (This is the folder that possesses the Python scripts that setup the S3-SQS bucket, and the daemon processing script both.)
* Dockerfile (This is the main docker image setup script, runs automatically with "$ docker compose up -d", utilize -d to keep using the same terminal.)
* Docker-compose.yml (This is the main docker compose YAML setup script that sets the Localstack services, which is an AWS server mockup, and the main video-qc-trio Service which possesses the programs, Bucket setup and daemon. Runs automatically with "$ docker compose up -d" as well together with the main dockerfile, utilize -d to keep using the same terminal.)

### 1) Docker image setup

* Dockerfile:

```dockerfile
#Step 0: Utilizes highly efficient minimal debian micro os just to run python scripts.
FROM python:3.11-slim 

WORKDIR /app

#Step 1: Copy and install Python dependencies (boto3, PyAV bundles its own FFmpeg libraries, python bundles pathlib and JSON)
RUN pip install --no-cache-dir av boto3

#Step 2: Copy the entire repository into /app
COPY . .

```

* Docker compose:

```yaml
services:
  localstack:
    image: localstack/localstack:3.0.0
    container_name: localstack_s3
    ports:
      - "127.0.0.1:4566:4566"
    environment:
      - SERVICES=s3,sqs
      - AWS_DEFAULT_REGION=us-east-1
        
  qc-app:
    build: .
    container_name: video_qc_trio
    depends_on:
      - localstack
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-1
    volumes:
      - .:/app
    command: tail -f /dev/null
```


Run the dockerfile and docker compose yml with:

```BASH
$ docker compose up -d 
```

And check the live services, which should be two (the localstack server, and the video-qc-trio service) with:

```BASH
$ docker ps
```


### 2) Localstack bucket setup (with s3 and sqs)

This step utilizes a one-time python script (s3_sqs_setup.py) that you must run by terminal (bash in linux) to setup:

- An S3 Bucket (`video-incoming`)
- An SQS Queue (`video-qc-queue`)
- An S3 Event Notification policy linking the bucket to the queue.

```python
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
```


Call it in terminal once with:

```BASH
$ docker exec -it video_qc_trio python "bucket_daemon_setup/s3_sqs_setup.py"
```


### In case the bucket enviroment setup failed in any stage:

* The reset
Since LocalStack stores mock AWS state in memory by default, tearing down the containers completely wipes every bucket, queue, and message created:

```Bash
docker compose down
```

#### Remember, if in any case the docker enviroment dies, it'll shut down the containers and the bucket designs. The setup thus must be done again as shown in this point 2 (and also 3 by activating the daemon script). 


### 3) Daemon script setup:

```Python
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
            MaxNumberOfMessages=1,   # Get 1 video job at a time
            WaitTimeSeconds=20,      # Long polling: Waits up to 20s if queue is empty
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
                    print(f"    - Bucket: {bucket_name}")
                    print(f"    - File Key: {object_key}")

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
```

Call it in terminal once with:

```BASH
$ docker exec -it video_qc_trio python "bucket_daemon_setup/processing_daemon.py"
```

# 4) Cloud structure online

#### In this moment, the terminal utilized by docker will freeze into the daemon process. If you're in an IDE, open a new terminal and execute a test file push onto the bucket to confirm the proper functioning of the cloud workflow.

Test push file for AnalyzerMK1:

```BASH
docker exec -it video_qc_trio python -c "import boto3; s3 = boto3.client('s3', endpoint_url='http://localstack:4566', region_name='us-east-1'); s3.upload_file('AnalyzerMK1/InputFolder/Test1.mp4', 'video-incoming', 'Test1.mp4')"
```

If within the "Analyzed" folder you see the JSON report appearing, the setup process is complete and the system is online working as intended.
#### Mind that in the processing_daemon.py script, the chosen program from the suite is hardcoded as the Analyzer initially in line 38 of the script, calling the function determined within the Analyzer ("batch_analyze_videos()") this is easily editable in an IDE, you can also stack the three of them and the three programs will run after one another, remember to call the functions that are improted on top of the daemon script.
#### The results of the processing for each program will be in it's respective output folder, it being "Analyzed", "Remuxed", or "Compliance_Report". This serves as a tidy automatical report organization system.