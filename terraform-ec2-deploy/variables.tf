# Simplified Variables for AWS Academy EC2 Deployment

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "taxiwatch"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ec2_ami_id" {
  description = "Ubuntu 22 AMI ID"
  type        = string
  default     = "ami-047f8ab1a8e4de3659"
}

variable "database_url" {
  description = "Database connection string (will use local PostgreSQL in Docker)"
  type        = string
  default     = "postgresql+asyncpg://postgres:postgres@localhost:5432/taxiwatch"
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

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
