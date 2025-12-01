#!/usr/bin/env python3
"""
Script to generate all remaining Terraform modules for TaxiWatch AWS deployment.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform" / "modules"

def create_file(file_path: Path, content: str):
    """Create a file with the given content."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    print(f"✅ {file_path.relative_to(BASE_DIR)}")

# =============================================================================
# Lambda Module
# =============================================================================

LAMBDA_MAIN_TF = '''# Lambda Module - API and Processing Functions

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "${var.project_name}-lambda-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Basic Lambda Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC Access Policy (for RDS and ElastiCache)
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Custom Policy for S3, SQS, Secrets Manager
resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "${var.project_name}-lambda-custom-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.frames_bucket_arn,
          "${var.frames_bucket_arn}/*",
          var.videos_bucket_arn,
          "${var.videos_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.ai_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_arn
      }
    ]
  })
}

# Security Group for Lambda
resource "aws_security_group" "lambda_sg" {
  name        = "${var.project_name}-${var.environment}-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-lambda-sg"
    Environment = var.environment
  }
}

# Lambda Layer for Dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename            = var.lambda_layer_zip
  layer_name          = "${var.project_name}-dependencies"
  compatible_runtimes = ["python3.12"]
  description         = "FastAPI, SQLAlchemy, and other dependencies"

  lifecycle {
    create_before_destroy = true
  }
}

# Main API Lambda Function
resource "aws_lambda_function" "api" {
  filename         = var.api_lambda_zip
  function_name    = "${var.project_name}-${var.environment}-api"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "app.lambda_handlers.api_handler.handler"
  source_code_hash = filebase64sha256(var.api_lambda_zip)
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 512

  layers = [aws_lambda_layer_version.dependencies.arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      DATABASE_URL       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${var.db_endpoint}/${var.db_name}"
      REDIS_URL         = "redis://${var.redis_endpoint}:6379/0"
      SECRET_KEY        = var.secret_key
      OPENAI_API_KEY    = var.openai_api_key
      ENVIRONMENT       = var.environment
      FRAMES_BUCKET     = var.frames_bucket_name
      VIDEOS_BUCKET     = var.videos_bucket_name
      AI_QUEUE_URL      = var.ai_queue_url
      CORS_ORIGINS      = var.cors_origins
    }
  }

  tags = {
    Name        = "${var.project_name}-api-lambda"
    Environment = var.environment
  }
}

# CloudWatch Log Group for API Lambda
resource "aws_cloudwatch_log_group" "api_lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-api-logs"
    Environment = var.environment
  }
}

# Frame Processor Lambda Function
resource "aws_lambda_function" "frame_processor" {
  filename         = var.api_lambda_zip
  function_name    = "${var.project_name}-${var.environment}-frame-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "app.lambda_handlers.frame_processor.handler"
  source_code_hash = filebase64sha256(var.api_lambda_zip)
  runtime         = "python3.12"
  timeout         = 300
  memory_size     = 1024

  layers = [aws_lambda_layer_version.dependencies.arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      DATABASE_URL    = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${var.db_endpoint}/${var.db_name}"
      OPENAI_API_KEY  = var.openai_api_key
      VIDEOS_BUCKET   = var.videos_bucket_name
      AI_QUEUE_URL    = var.ai_queue_url
    }
  }

  tags = {
    Name        = "${var.project_name}-frame-processor"
    Environment = var.environment
  }
}

# S3 Trigger Permission for Frame Processor
resource "aws_lambda_permission" "allow_s3_frames" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.frame_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.frames_bucket_arn
}

# CloudWatch Log Group for Frame Processor
resource "aws_cloudwatch_log_group" "frame_processor_logs" {
  name              = "/aws/lambda/${aws_lambda_function.frame_processor.function_name}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-frame-processor-logs"
    Environment = var.environment
  }
}
'''

LAMBDA_VARIABLES_TF = '''variable "project_name" {
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
'''

LAMBDA_OUTPUTS_TF = '''output "api_lambda_arn" {
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
'''

# =============================================================================
# API Gateway Module
# =============================================================================

API_GATEWAY_MAIN_TF = '''# API Gateway HTTP API Module

resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "TaxiWatch API Gateway"

  cors_configuration {
    allow_origins = var.cors_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Requested-With"]
    expose_headers = ["Content-Length", "Content-Type"]
    max_age       = 300
  }

  tags = {
    Name        = "${var.project_name}-api-gateway"
    Environment = var.environment
  }
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.lambda_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Default Route (catch all)
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Deployment Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  default_route_settings {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }

  tags = {
    Name        = "${var.project_name}-api-stage"
    Environment = var.environment
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-api-gateway-logs"
    Environment = var.environment
  }
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Custom Domain (Optional)
resource "aws_apigatewayv2_domain_name" "main" {
  count       = var.custom_domain_name != "" ? 1 : 0
  domain_name = var.custom_domain_name

  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = {
    Name        = "${var.project_name}-custom-domain"
    Environment = var.environment
  }
}

# API Mapping (Optional)
resource "aws_apigatewayv2_api_mapping" "main" {
  count       = var.custom_domain_name != "" ? 1 : 0
  api_id      = aws_apigatewayv2_api.main.id
  domain_name = aws_apigatewayv2_domain_name.main[0].id
  stage       = aws_apigatewayv2_stage.default.id
}
'''

API_GATEWAY_VARIABLES_TF = '''variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "custom_domain_name" {
  description = "Custom domain name for API (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (optional)"
  type        = string
  default     = ""
}
'''

API_GATEWAY_OUTPUTS_TF = '''output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}

output "api_arn" {
  description = "API Gateway ARN"
  value       = aws_apigatewayv2_api.main.arn
}

output "custom_domain_name" {
  description = "Custom domain name (if configured)"
  value       = var.custom_domain_name != "" ? aws_apigatewayv2_domain_name.main[0].domain_name : ""
}
'''

# =============================================================================
# S3 Module
# =============================================================================

S3_MAIN_TF = '''# S3 Buckets for Frames, Videos, and Static Files

# Frames Bucket (Short retention - 7 days)
resource "aws_s3_bucket" "frames" {
  bucket = "${var.project_name}-${var.environment}-frames"

  tags = {
    Name        = "${var.project_name}-frames"
    Environment = var.environment
    Purpose     = "ESP32 camera frames"
  }
}

resource "aws_s3_bucket_versioning" "frames" {
  bucket = aws_s3_bucket.frames.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "frames" {
  bucket = aws_s3_bucket.frames.id

  rule {
    id     = "delete-old-frames"
    status = "Enabled"

    expiration {
      days = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

resource "aws_s3_bucket_notification" "frames" {
  bucket = aws_s3_bucket.frames.id

  lambda_function {
    lambda_function_arn = var.frame_processor_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".jpg"
  }

  depends_on = [var.lambda_s3_permission]
}

# Videos Bucket (Long retention with Glacier transition)
resource "aws_s3_bucket" "videos" {
  bucket = "${var.project_name}-${var.environment}-videos"

  tags = {
    Name        = "${var.project_name}-videos"
    Environment = var.environment
    Purpose     = "Video archives"
  }
}

resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "archive-to-glacier"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 180
    }
  }
}

# Static Files Bucket (Frontend assets, reports, etc.)
resource "aws_s3_bucket" "static" {
  bucket = "${var.project_name}-${var.environment}-static"

  tags = {
    Name        = "${var.project_name}-static"
    Environment = var.environment
    Purpose     = "Static files and reports"
  }
}

resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access for all buckets
resource "aws_s3_bucket_public_access_block" "frames" {
  bucket = aws_s3_bucket.frames.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket = aws_s3_bucket.videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "frames" {
  bucket = aws_s3_bucket.frames.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
'''

S3_VARIABLES_TF = '''variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "frame_processor_lambda_arn" {
  description = "Frame processor Lambda ARN for S3 notifications"
  type        = string
}

variable "lambda_s3_permission" {
  description = "Lambda S3 permission resource (for depends_on)"
  type        = any
}
'''

S3_OUTPUTS_TF = '''output "frames_bucket_name" {
  description = "Frames bucket name"
  value       = aws_s3_bucket.frames.id
}

output "frames_bucket_arn" {
  description = "Frames bucket ARN"
  value       = aws_s3_bucket.frames.arn
}

output "videos_bucket_name" {
  description = "Videos bucket name"
  value       = aws_s3_bucket.videos.id
}

output "videos_bucket_arn" {
  description = "Videos bucket ARN"
  value       = aws_s3_bucket.videos.arn
}

output "static_bucket_name" {
  description = "Static files bucket name"
  value       = aws_s3_bucket.static.id
}

output "static_bucket_arn" {
  description = "Static files bucket ARN"
  value       = aws_s3_bucket.static.arn
}
'''

# =============================================================================
# SQS Module
# =============================================================================

SQS_MAIN_TF = '''# SQS Queue for AI Processing

# Main AI Analysis Queue
resource "aws_sqs_queue" "ai_analysis" {
  name                       = "${var.project_name}-${var.environment}-ai-analysis"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10       # Long polling
  visibility_timeout_seconds = 300      # 5 minutes (match Lambda timeout)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ai_analysis_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-ai-queue"
    Environment = var.environment
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "ai_analysis_dlq" {
  name                       = "${var.project_name}-${var.environment}-ai-analysis-dlq"
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10

  tags = {
    Name        = "${var.project_name}-ai-dlq"
    Environment = var.environment
  }
}

# CloudWatch Alarm for DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-${var.environment}-dlq-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert when messages appear in DLQ"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.ai_analysis_dlq.name
  }

  tags = {
    Name        = "${var.project_name}-dlq-alarm"
    Environment = var.environment
  }
}
'''

SQS_VARIABLES_TF = '''variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}
'''

SQS_OUTPUTS_TF = '''output "ai_queue_url" {
  description = "AI analysis queue URL"
  value       = aws_sqs_queue.ai_analysis.url
}

output "ai_queue_arn" {
  description = "AI analysis queue ARN"
  value       = aws_sqs_queue.ai_analysis.arn
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = aws_sqs_queue.ai_analysis_dlq.url
}

output "dlq_arn" {
  description = "Dead letter queue ARN"
  value       = aws_sqs_queue.ai_analysis_dlq.arn
}
'''

# =============================================================================
# ElastiCache Module
# =============================================================================

ELASTICACHE_MAIN_TF = '''# ElastiCache Redis for Caching and Session Storage

# Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-${var.environment}-redis-subnet"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-redis-subnet"
    Environment = var.environment
  }
}

# Security Group
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
    description     = "Redis access from Lambda"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-redis-sg"
    Environment = var.environment
  }
}

# Parameter Group
resource "aws_elasticache_parameter_group" "redis" {
  name   = "${var.project_name}-${var.environment}-redis-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name        = "${var.project_name}-redis-params"
    Environment = var.environment
  }
}

# Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.node_type
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
  port                 = 6379

  tags = {
    Name        = "${var.project_name}-redis"
    Environment = var.environment
  }
}
'''

ELASTICACHE_VARIABLES_TF = '''variable "project_name" {
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
  description = "Private subnet IDs for ElastiCache"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "Security groups allowed to access Redis"
  type        = list(string)
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}
'''

ELASTICACHE_OUTPUTS_TF = '''output "redis_endpoint" {
  description = "Redis endpoint address"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}
'''

# =============================================================================
# Secrets Manager Module
# =============================================================================

SECRETS_MAIN_TF = '''# AWS Secrets Manager for Sensitive Configuration

resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-${var.environment}-secrets"
  description = "Application secrets for TaxiWatch"

  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-secrets"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    SECRET_KEY     = var.secret_key
    OPENAI_API_KEY = var.openai_api_key
    DB_PASSWORD    = var.db_password
  })
}
'''

SECRETS_VARIABLES_TF = '''variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
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

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
'''

SECRETS_OUTPUTS_TF = '''output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "secrets_name" {
  description = "Secrets Manager name"
  value       = aws_secretsmanager_secret.app_secrets.name
}
'''

# =============================================================================
# Main - Write all files
# =============================================================================

def main():
    print("🚀 Generating Terraform modules...\n")

    # Lambda Module
    print("📦 Lambda Module:")
    create_file(TERRAFORM_DIR / "lambda" / "main.tf", LAMBDA_MAIN_TF)
    create_file(TERRAFORM_DIR / "lambda" / "variables.tf", LAMBDA_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "lambda" / "outputs.tf", LAMBDA_OUTPUTS_TF)

    # API Gateway Module
    print("\n🌐 API Gateway Module:")
    create_file(TERRAFORM_DIR / "api_gateway" / "main.tf", API_GATEWAY_MAIN_TF)
    create_file(TERRAFORM_DIR / "api_gateway" / "variables.tf", API_GATEWAY_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "api_gateway" / "outputs.tf", API_GATEWAY_OUTPUTS_TF)

    # S3 Module
    print("\n💾 S3 Module:")
    create_file(TERRAFORM_DIR / "s3" / "main.tf", S3_MAIN_TF)
    create_file(TERRAFORM_DIR / "s3" / "variables.tf", S3_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "s3" / "outputs.tf", S3_OUTPUTS_TF)

    # SQS Module
    print("\n📬 SQS Module:")
    create_file(TERRAFORM_DIR / "sqs" / "main.tf", SQS_MAIN_TF)
    create_file(TERRAFORM_DIR / "sqs" / "variables.tf", SQS_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "sqs" / "outputs.tf", SQS_OUTPUTS_TF)

    # ElastiCache Module
    print("\n🗄️ ElastiCache Module:")
    create_file(TERRAFORM_DIR / "elasticache" / "main.tf", ELASTICACHE_MAIN_TF)
    create_file(TERRAFORM_DIR / "elasticache" / "variables.tf", ELASTICACHE_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "elasticache" / "outputs.tf", ELASTICACHE_OUTPUTS_TF)

    # Secrets Manager Module
    print("\n🔐 Secrets Manager Module:")
    create_file(TERRAFORM_DIR / "secrets" / "main.tf", SECRETS_MAIN_TF)
    create_file(TERRAFORM_DIR / "secrets" / "variables.tf", SECRETS_VARIABLES_TF)
    create_file(TERRAFORM_DIR / "secrets" / "outputs.tf", SECRETS_OUTPUTS_TF)

    print("\n✅ All Terraform modules generated successfully!")
    print("\n📋 Total: 18 files created")

if __name__ == "__main__":
    main()
