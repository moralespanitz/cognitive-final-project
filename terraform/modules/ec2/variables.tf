variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EC2 will be deployed"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for EC2"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ami_id" {
  description = "Ubuntu 22 AMI ID"
  type        = string
  default     = "ami-047f8ab1a8e4de3659"  # Cloud9Ubuntu22 in us-west-2
}

variable "key_name" {
  description = "EC2 key pair name (leave empty to create new)"
  type        = string
  default     = ""
}

variable "rds_endpoint" {
  description = "RDS database endpoint"
  type        = string
}

variable "rds_security_group_id" {
  description = "RDS security group ID"
  type        = string
}

variable "s3_frames_bucket" {
  description = "S3 bucket for frames"
  type        = string
}

variable "s3_videos_bucket" {
  description = "S3 bucket for videos"
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
