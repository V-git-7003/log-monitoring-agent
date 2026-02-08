# Log Monitoring Agent

An AWS-based log monitoring and root cause analysis (RCA) system that automatically detects and correlates incidents across multiple services using CloudWatch Logs.

## Overview

This project demonstrates automated incident detection by:
1. Generating mock incident logs across multiple AWS services (RDS, ECS, Application)
2. Using Lambda to analyze and correlate these logs
3. Performing automated root cause analysis

## Architecture

```
┌─────────────────┐
│  ECS Fargate    │
│  (Mock Logs)    │──► CloudWatch Logs
└─────────────────┘      │
                         │
┌─────────────────┐      │
│  EventBridge    │      │
│  (Schedule)     │──────┼────► Lambda Function
└─────────────────┘      │      (RCA Agent)
                         │          │
                         └──────────┘
                         
CloudWatch Log Groups:
  • /ecs/my-python-service
  • /aws/ecs/containerinsights/my-cluster/performance
  • /aws/rds/instance/mydb/postgresql
```

## Features

- **Mock Log Generator**: ECS task that simulates a cascading failure scenario
- **Automated Log Analysis**: Lambda function that searches and correlates logs
- **Root Cause Detection**: Identifies patterns like "RDS max connections → app timeouts → ECS restarts"
- **Scheduled Monitoring**: EventBridge trigger runs analysis every 5 minutes
- **Infrastructure as Code**: Fully automated deployment using Terraform

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.5.x
- Docker (for building ECS container image)
- GitHub CLI (`gh`) for authentication (optional)

## Setup

### 1. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review and apply infrastructure
terraform apply
```

This creates:
- ECR repository for Docker images
- ECS cluster and task definition
- Lambda function with IAM roles
- CloudWatch log groups
- EventBridge scheduling rule

### 2. Build and Push Docker Image

```bash
# Build for AMD64 architecture and push to ECR
./build-and-push.sh
```

### 3. Run Mock Log Generator

**Option A: Run ECS task manually from AWS Console**
1. Navigate to ECS → Clusters → log-monitoring-cluster
2. Click "Run new task"
3. Select:
   - Launch type: Fargate
   - Task definition: mock-cloudwatch-logs
   - Cluster VPC and subnets (use defaults)
   - Assign public IP: Yes

**Option B: Run via AWS CLI**
```bash
aws ecs run-task \
  --cluster log-monitoring-cluster \
  --task-definition mock-cloudwatch-logs \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],assignPublicIp=ENABLED}" \
  --region ap-south-1
```

### 4. Test Lambda Function

The Lambda runs automatically every 5 minutes via EventBridge, or test manually:

```bash
aws lambda invoke \
  --function-name log-rca-agent \
  --region ap-south-1 \
  output.json && cat output.json
```

Check the logs:
```bash
aws logs tail /aws/lambda/log-rca-agent --follow --region ap-south-1
```

## How It Works

### Incident Simulation

The ECS task generates a cascading failure scenario:

1. **RDS Error**: `WARN: Maximum connections exceeded for database mydb`
2. **App Error**: `ERROR: psycopg2.OperationalError: could not connect to server`
3. **ECS Health Check Failure**: `INFO: Task stopped due to failed ELB health check`

### Log Analysis

The Lambda function:
1. Retrieves logs from all three CloudWatch log groups
2. Searches for error patterns using string matching
3. Correlates errors across services
4. Outputs RCA if all three error types are detected

### Expected Output

When all errors are detected:
```
RCA: RDS max connections exceeded → app timeouts → ECS restarts
```

## Project Structure

```
.
├── ecr.tf                      # ECR repository for Docker images
├── ecs.tf                      # ECS cluster and task definition
├── eventbridge.tf              # Scheduled Lambda triggers
├── iam.tf                      # IAM roles and policies
├── iam_ecs_execution_role.tf   # ECS execution role
├── iam_task_policy.tf          # CloudWatch write permissions
├── iam_task_role.tf            # ECS task role
├── lambda.tf                   # Lambda function definition
├── main.tf                     # AWS provider configuration
├── output.tf                   # Terraform outputs
├── build-and-push.sh           # Docker build and push script
├── lambda/
│   └── handler.py              # Lambda RCA logic
└── mock-logs/
    ├── Dockerfile              # Container image definition
    ├── mock_cloudwatch_logs.py # Log generator script
    └── requirements.txt        # Python dependencies
```

## Configuration

### Region
Default: `ap-south-1` (Mumbai)  
To change, update `main.tf`:
```hcl
provider "aws" {
  region = "us-east-1"  # your preferred region
}
```

### Lambda Schedule
Default: Every 5 minutes  
To change, update `eventbridge.tf`:
```hcl
schedule_expression = "rate(10 minutes)"  # or "cron(0 12 * * ? *)"
```

## Cleanup

Remove all AWS resources:
```bash
# Delete ECS tasks first (if any running)
# Then destroy infrastructure
terraform destroy
```

## Troubleshooting

### Lambda not detecting logs
- Check the time window in `lambda/handler.py` (currently searches -12h to +6h)
- Verify logs exist in CloudWatch log groups
- Check Lambda IAM permissions for `logs:FilterLogEvents`

### ECS task fails to start
- Ensure Docker image is pushed to ECR
- Check ECS task logs in CloudWatch
- Verify security group allows egress traffic

### Docker build errors
- Ensure building with `--platform linux/amd64` for Fargate compatibility
- Check Docker daemon is running

## License

MIT

## Contributing

Pull requests welcome! For major changes, please open an issue first.
