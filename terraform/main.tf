provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "Bousbis Tiny Tale Machine"
      ManagedBy = "Terraform"
      Challenge = "AWS Weekend Creative Challenge"
    }
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 7
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
  source_code_hash               = data.archive_file.lambda.output_base64sha256
  reserved_concurrent_executions = var.max_concurrency

  depends_on = [
    aws_iam_role_policy_attachment.basic_execution,
    aws_cloudwatch_log_group.lambda,
  ]
}

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
