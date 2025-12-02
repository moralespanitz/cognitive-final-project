# Minimal TaxiWatch API - Lambda + API Gateway only
# Works with AWS Lab accounts with limited permissions

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "taxiwatch"
}

variable "environment" {
  default = "prod"
}

# Lambda Layer for dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename            = var.lambda_layer_zip
  layer_name          = "${var.project_name}-${var.environment}-dependencies"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256(var.lambda_layer_zip)
}

variable "lambda_layer_zip" {
  default = "../backend/lambda_layer.zip"
}

variable "api_lambda_zip" {
  default = "../backend/lambda_package.zip"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
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
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "api" {
  filename         = var.api_lambda_zip
  function_name    = "${var.project_name}-${var.environment}-api"
  role             = aws_iam_role.lambda_role.arn
  handler          = "app.main.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512
  source_code_hash = filebase64sha256(var.api_lambda_zip)

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      DEBUG         = "false"
      SECRET_KEY    = var.secret_key
      CORS_ORIGINS  = "*"
      # No database - using in-memory storage for video frames
    }
  }
}

variable "secret_key" {
  description = "Secret key for JWT"
  default     = "dev-secret-key-change-in-production"
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "TaxiWatch API Gateway"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Route-ID"]
    max_age       = 300
  }
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# Default Route
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL - use this for ESP32"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

output "esp32_upload_url" {
  description = "Full URL for ESP32 to upload frames"
  value       = "${aws_apigatewayv2_stage.default.invoke_url}/api/v1/video/device/upload"
}
