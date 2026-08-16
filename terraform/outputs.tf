output "lambda_function_url" {
  description = "Copy this value into frontend/config.js."
  value       = aws_lambda_function_url.story_generator.function_url
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function."
  value       = aws_lambda_function.story_generator.function_name
}
