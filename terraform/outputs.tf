# Terraform Outputs

# API Gateway
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_id" {
  description = "API Gateway ID"
  value       = module.api_gateway.api_id
}

output "custom_domain" {
  description = "Custom domain name (if configured)"
  value       = module.api_gateway.custom_domain_name
}

# Lambda
output "api_lambda_arn" {
  description = "API Lambda function ARN"
  value       = module.lambda.api_lambda_arn
}

output "api_lambda_name" {
  description = "API Lambda function name"
  value       = module.lambda.api_lambda_name
}

output "frame_processor_lambda_arn" {
  description = "Frame processor Lambda ARN"
  value       = module.lambda.frame_processor_lambda_arn
}

# RDS
output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_endpoint
}

output "db_address" {
  description = "Database address"
  value       = module.rds.db_address
}

# ElastiCache
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.redis_endpoint
}

# S3
output "frames_bucket_name" {
  description = "Frames S3 bucket name"
  value       = module.s3.frames_bucket_name
}

output "videos_bucket_name" {
  description = "Videos S3 bucket name"
  value       = module.s3.videos_bucket_name
}

output "static_bucket_name" {
  description = "Static files S3 bucket name"
  value       = module.s3.static_bucket_name
}

# SQS
output "ai_queue_url" {
  description = "AI analysis queue URL"
  value       = module.sqs.ai_queue_url
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = module.sqs.dlq_url
}

# VPC
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

# Secrets Manager
output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = module.secrets.secrets_arn
}
