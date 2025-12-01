output "api_lambda_arn" {
  description = "API Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "api_lambda_invoke_arn" {
  description = "API Lambda function invoke ARN"
  value       = aws_lambda_function.api.invoke_arn
}

output "api_lambda_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "frame_processor_lambda_arn" {
  description = "Frame processor Lambda ARN"
  value       = aws_lambda_function.frame_processor.arn
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "lambda_security_group_id" {
  description = "Lambda security group ID"
  value       = aws_security_group.lambda_sg.id
}
