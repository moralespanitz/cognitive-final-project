# TaxiWatch - Complete AWS Infrastructure

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name        = var.project_name
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  project_name   = var.project_name
  environment    = var.environment
  secret_key     = var.secret_key
  openai_api_key = var.openai_api_key
  db_password    = var.db_password
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  database_subnet_ids   = module.vpc.database_subnet_ids
  allowed_security_groups = []  # Will be updated after Lambda module
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  multi_az              = var.db_multi_az
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"

  project_name            = var.project_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  private_subnet_ids      = module.vpc.private_subnet_ids
  allowed_security_groups = []  # Will be updated after Lambda module
  node_type               = var.redis_node_type
}

# SQS Module
module "sqs" {
  source = "./modules/sqs"

  project_name = var.project_name
  environment  = var.environment
}

# S3 Module (must be created before Lambda due to notifications)
module "s3" {
  source = "./modules/s3"

  project_name               = var.project_name
  environment                = var.environment
  frame_processor_lambda_arn = module.lambda.frame_processor_lambda_arn
  lambda_s3_permission       = null  # Circular dependency resolved below
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  db_endpoint         = module.rds.db_endpoint
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  redis_endpoint      = module.elasticache.redis_endpoint
  secret_key          = var.secret_key
  openai_api_key      = var.openai_api_key
  frames_bucket_name  = module.s3.frames_bucket_name
  frames_bucket_arn   = module.s3.frames_bucket_arn
  videos_bucket_name  = module.s3.videos_bucket_name
  videos_bucket_arn   = module.s3.videos_bucket_arn
  ai_queue_url        = module.sqs.ai_queue_url
  ai_queue_arn        = module.sqs.ai_queue_arn
  secrets_arn         = module.secrets.secrets_arn
  cors_origins        = var.cors_origins
  api_lambda_zip      = var.api_lambda_zip
  lambda_layer_zip    = var.lambda_layer_zip
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name         = var.project_name
  environment          = var.environment
  lambda_invoke_arn    = module.lambda.api_lambda_invoke_arn
  lambda_function_name = module.lambda.api_lambda_name
  cors_origins         = var.cors_origins_list
  custom_domain_name   = var.custom_domain_name
  certificate_arn      = var.certificate_arn
}

# Update RDS security group to allow Lambda access
resource "aws_security_group_rule" "rds_from_lambda" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = module.rds.db_security_group_id
  source_security_group_id = module.lambda.lambda_security_group_id
  description              = "PostgreSQL access from Lambda"
}

# Update ElastiCache security group to allow Lambda access
resource "aws_security_group_rule" "redis_from_lambda" {
  type                     = "ingress"
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
  security_group_id        = module.elasticache.redis_security_group_id
  source_security_group_id = module.lambda.lambda_security_group_id
  description              = "Redis access from Lambda"
}
