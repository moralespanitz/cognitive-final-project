# Lambda Module - API and Processing Functions

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
