import boto3
from datetime import datetime, timedelta

logs = boto3.client("logs")

def get_logs(log_group):
    # Use a wider time window to account for clock skew
    end_time = int(datetime.utcnow().timestamp() * 1000) + (6 * 60 * 60 * 1000)  # +6 hours
    start_time = int((datetime.utcnow() - timedelta(hours=12)).timestamp() * 1000)  # -12 hours

    try:
        response = logs.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
        )
        
        events = response.get("events", [])
        print(f"Retrieved {len(events)} events from {log_group}")
        return [e["message"] for e in events]
    except Exception as e:
        print(f"Error reading {log_group}: {str(e)}")
        return []

def lambda_handler(event, context):
    app_logs = get_logs("/ecs/my-python-service")
    ecs_logs = get_logs("/aws/ecs/containerinsights/my-cluster/performance")
    rds_logs = get_logs("/aws/rds/instance/mydb/postgresql")

    print(f"Found {len(app_logs)} app logs")
    print(f"Found {len(ecs_logs)} ecs logs")
    print(f"Found {len(rds_logs)} rds logs")
    
    if app_logs:
        print(f"Sample app log: {app_logs[0]}")
    if ecs_logs:
        print(f"Sample ecs log: {ecs_logs[0]}")
    if rds_logs:
        print(f"Sample rds log: {rds_logs[0]}")

    errors = []

    if any("could not connect" in l for l in app_logs):
        errors.append("db_client_error")

    if any("health check" in l.lower() for l in ecs_logs):
        errors.append("ecs_health_error")

    if any("Maximum connections" in l for l in rds_logs):
        errors.append("db_capacity_error")

    if set(errors) == {
        "db_client_error",
        "ecs_health_error",
        "db_capacity_error"
    }:
        print("RCA: RDS max connections exceeded → app timeouts → ECS restarts")
    else:
        print("No major incident detected")

    return {"status": "ok"}
