variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Lambda"
  type        = list(string)
}

variable "db_endpoint" {
  description = "RDS endpoint"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  type        = string
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "frames_bucket_name" {
  description = "S3 bucket name for frames"
  type        = string
}

variable "frames_bucket_arn" {
  description = "S3 bucket ARN for frames"
  type        = string
}

variable "videos_bucket_name" {
  description = "S3 bucket name for videos"
  type        = string
}

variable "videos_bucket_arn" {
  description = "S3 bucket ARN for videos"
  type        = string
}

variable "ai_queue_url" {
  description = "SQS queue URL for AI processing"
  type        = string
}

variable "ai_queue_arn" {
  description = "SQS queue ARN for AI processing"
  type        = string
}

variable "secrets_arn" {
  description = "Secrets Manager ARN"
  type        = string
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = string
  default     = "*"
}

variable "api_lambda_zip" {
  description = "Path to API Lambda deployment package"
  type        = string
  default     = "../backend/lambda_package.zip"
}

variable "lambda_layer_zip" {
  description = "Path to Lambda layer deployment package"
  type        = string
  default     = "../backend/lambda_layer.zip"
}
