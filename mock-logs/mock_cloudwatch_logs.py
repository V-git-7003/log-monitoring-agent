import boto3
import time
from datetime import datetime

logs_client = boto3.client("logs", region_name="ap-south-1")

def ensure_log_group(log_group):
    try:
        logs_client.create_log_group(logGroupName=log_group)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass

def ensure_log_stream(log_group, log_stream):
    try:
        logs_client.create_log_stream(
            logGroupName=log_group,
            logStreamName=log_stream
        )
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass

def put_log_event(log_group, log_stream, message, sequence_token=None):
    event = {
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "message": message
    }

    args = {
        "logGroupName": log_group,
        "logStreamName": log_stream,
        "logEvents": [event]
    }

    if sequence_token:
        args["sequenceToken"] = sequence_token

    response = logs_client.put_log_events(**args)
    return response.get("nextSequenceToken")

# ----------------------------------------------------
# Log groups & streams
# ----------------------------------------------------

LOGS = {
    "app": {
        "group": "/ecs/my-python-service",
        "stream": "app-container-1"
    },
    "ecs": {
        "group": "/aws/ecs/containerinsights/my-cluster/performance",
        "stream": "ecs-agent"
    },
    "rds": {
        "group": "/aws/rds/instance/mydb/postgresql",
        "stream": "postgresql.log"
    }
}

# Create groups & streams
for item in LOGS.values():
    ensure_log_group(item["group"])
    ensure_log_stream(item["group"], item["stream"])

# ----------------------------------------------------
# Mock incident timeline
# ----------------------------------------------------

tokens = {}

print("🚨 Injecting mock incident logs...\n")

# Step 1: RDS runs out of connections
tokens["rds"] = put_log_event(
    LOGS["rds"]["group"],
    LOGS["rds"]["stream"],
    "WARN: Maximum connections exceeded for database mydb"
)
time.sleep(1)

# Step 2: App starts failing DB connections
tokens["app"] = put_log_event(
    LOGS["app"]["group"],
    LOGS["app"]["stream"],
    "ERROR db.py:45 psycopg2.OperationalError: could not connect to server: Connection timed out"
)
time.sleep(1)

# Step 3: ECS health check fails
tokens["ecs"] = put_log_event(
    LOGS["ecs"]["group"],
    LOGS["ecs"]["stream"],
    "INFO Task stopped due to failed ELB health check"
)

print("✅ Mock logs successfully pushed to CloudWatch")
