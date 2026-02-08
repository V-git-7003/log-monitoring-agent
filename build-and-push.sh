#!/bin/bash
set -e

# Get ECR repository URL from terraform output
ECR_REPO=$(terraform output -raw ecr_repository_url)
REGION="ap-south-1"

echo "Building Docker image for AMD64 architecture..."
cd mock-logs
docker build --platform linux/amd64 -t mock-cloudwatch-logs .

echo "Tagging image..."
docker tag mock-cloudwatch-logs:latest $ECR_REPO:latest

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

echo "Pushing image to ECR..."
docker push $ECR_REPO:latest

echo "Done! Image pushed to $ECR_REPO:latest"
