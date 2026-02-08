resource "aws_iam_policy" "cloudwatch_write" {
  name = "mock-cloudwatch-logs-write"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cloudwatch_write" {
  role       = aws_iam_role.mock_logs_task_role.name
  policy_arn = aws_iam_policy.cloudwatch_write.arn
}
