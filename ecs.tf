resource "aws_ecs_cluster" "main" {
  name = "log-monitoring-cluster"

  tags = {
    Project = "log-rca-hackathon"
  }
}

resource "aws_ecs_task_definition" "mock_logs" {
  family                   = "mock-cloudwatch-logs"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  execution_role_arn = aws_iam_role.ecs_execution_role.arn
  task_role_arn      = aws_iam_role.mock_logs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "mock-cloudwatch-logs"
      image     = "${aws_ecr_repository.mock_logs.repository_url}:latest"
      essential = true

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/mock-cloudwatch-logs"
          awslogs-region        = "ap-south-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}