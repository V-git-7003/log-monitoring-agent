resource "aws_ecr_repository" "mock_logs" {
  name = "mock-cloudwatch-logs"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project = "log-rca-hackathon"
  }
}
