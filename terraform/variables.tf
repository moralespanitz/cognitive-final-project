# Terraform Variables for TaxiWatch Infrastructure

# General
variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "taxiwatch"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24"]
}

# RDS Configuration
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "taxiwatch"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "taxiwatch_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

# Application Secrets
variable "secret_key" {
  description = "Application secret key for JWT signing"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for GPT-4 and Vision"
  type        = string
  sensitive   = true
}

# CORS Configuration
variable "cors_origins" {
  description = "CORS allowed origins (comma-separated string for Lambda env)"
  type        = string
  default     = "http://localhost:3000,https://taxiwatch.example.com"
}

variable "cors_origins_list" {
  description = "CORS allowed origins (list for API Gateway)"
  type        = list(string)
  default     = ["http://localhost:3000", "https://taxiwatch.example.com"]
}

# Lambda Configuration
variable "api_lambda_zip" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = "../backend/lambda_package.zip"
}

variable "lambda_layer_zip" {
  description = "Path to Lambda layer package"
  type        = string
  default     = "../backend/lambda_layer.zip"
}

# Custom Domain (Optional)
variable "custom_domain_name" {
  description = "Custom domain name for API Gateway (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (optional)"
  type        = string
  default     = ""
}
