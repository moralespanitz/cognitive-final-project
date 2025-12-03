# TaxiWatch - AWS Infrastructure with EC2
# Simplified deployment: EC2 + RDS + S3 (No Lambda, No Redis)

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name          = var.project_name
  environment           = var.environment
  vpc_cidr              = var.vpc_cidr
  availability_zones    = var.availability_zones
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
}

# S3 Module (for video frames and archives)
module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment

  # No Lambda integration needed for EC2
  frame_processor_lambda_arn = null
  lambda_s3_permission       = null
}

# RDS Module (PostgreSQL database)
module "rds" {
  source = "./modules/rds"

  project_name            = var.project_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  database_subnet_ids     = module.vpc.database_subnet_ids
  allowed_security_groups = []  # Will be added by EC2 module
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  multi_az                = var.db_multi_az
}

# EC2 Module (Application server)
module "ec2" {
  source = "./modules/ec2"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids

  # Instance configuration
  instance_type = var.ec2_instance_type
  ami_id        = var.ec2_ami_id
  key_name      = var.ec2_key_name

  # Database connection
  rds_endpoint          = module.rds.db_endpoint
  rds_security_group_id = module.rds.db_security_group_id
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password

  # S3 buckets
  s3_frames_bucket = module.s3.frames_bucket_name
  s3_videos_bucket = module.s3.videos_bucket_name

  # Application secrets
  secret_key = var.secret_key

  # Repository configuration
  github_repo   = var.github_repo
  github_branch = var.github_branch

  depends_on = [module.vpc, module.rds, module.s3]
}
