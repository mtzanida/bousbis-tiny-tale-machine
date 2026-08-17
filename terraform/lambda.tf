# Package the function code into a zip before deployment.
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "story_generator" {
  filename                       = data.archive_file.lambda.output_path
  function_name                  = var.project_name
  role                           = aws_iam_role.lambda.arn
  handler                        = "lambda_function.lambda_handler"
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  memory_size                    = 128
  timeout                        = 5
  source_code_hash = data.archive_file.lambda.output_base64sha256

  # Uncomment after requesting a Lambda concurrency quota increase (Service Quotas → Lambda → Concurrent executions).
  # reserved_concurrent_executions = var.max_concurrency

  depends_on = [
    aws_iam_role_policy_attachment.basic_execution,
    aws_cloudwatch_log_group.lambda,
  ]
}

# Public HTTPS endpoint — no API Gateway needed.
resource "aws_lambda_function_url" "story_generator" {
  function_name      = aws_lambda_function.story_generator.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = [var.allowed_origin]
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
    max_age       = 3600
  }
}
