FROM python:3.11-slim

WORKDIR /app

# Step 1: Copy and install Python dependencies (boto3, PyAV bundles its own FFmpeg libraries, python bundles pathlib and JSON)
RUN pip install --no-cache-dir av boto3

# Step 2: Copy the entire repository into /app
COPY . .