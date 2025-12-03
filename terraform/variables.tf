# Terraform Variables for TaxiWatch EC2 Deployment

# General
variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "taxiwatch"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"  # Oregon - from screenshot
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
  default     = ["us-west-2a", "us-west-2b"]
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

# EC2 Configuration
variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"  # ~$15/month
}

variable "ec2_ami_id" {
  description = "Ubuntu 22 AMI ID (Cloud9Ubuntu22)"
  type        = string
  default     = "ami-047f8ab1a8e4de3659"  # us-west-2
}

variable "ec2_key_name" {
  description = "EC2 key pair name (leave empty to auto-generate)"
  type        = string
  default     = ""  # Will create new key pair
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
  default     = "db.t3.micro"  # Free tier eligible
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20  # Free tier: 20GB
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false  # Save costs for MVP
}

# Application Secrets
variable "secret_key" {
  description = "Application secret key for JWT signing"
  type        = string
  sensitive   = true
}

# GitHub Repository
variable "github_repo" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/moralespanitz/cognitive-final-project.git"
}

variable "github_branch" {
  description = "GitHub branch to deploy"
  type        = string
  default     = "master"
}
