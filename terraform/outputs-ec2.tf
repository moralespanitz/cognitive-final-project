# Terraform Outputs for TaxiWatch EC2 Deployment

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = var.db_name
}

# S3 Outputs
output "s3_frames_bucket" {
  description = "S3 bucket for video frames"
  value       = module.s3.frames_bucket_name
}

output "s3_videos_bucket" {
  description = "S3 bucket for video archives"
  value       = module.s3.videos_bucket_name
}

# EC2 Outputs
output "ec2_public_ip" {
  description = "EC2 Elastic IP (public)"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = module.ec2.instance_id
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = module.ec2.ssh_command
}

output "private_key_path" {
  description = "Path to SSH private key (if auto-generated)"
  value       = module.ec2.private_key_path
}

# Application URLs
output "frontend_url" {
  description = "Frontend application URL"
  value       = module.ec2.frontend_url
}

output "backend_url" {
  description = "Backend API URL"
  value       = module.ec2.backend_url
}

output "backend_docs_url" {
  description = "Backend API documentation URL"
  value       = module.ec2.backend_docs_url
}

# Connection String (for manual setup)
output "database_connection_string" {
  description = "Database connection string (sensitive)"
  value       = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
  sensitive   = true
}

# Deployment Information
output "deployment_info" {
  description = "Quick deployment information"
  value = {
    region         = var.aws_region
    environment    = var.environment
    frontend       = module.ec2.frontend_url
    backend        = module.ec2.backend_url
    docs           = module.ec2.backend_docs_url
    ssh            = module.ec2.ssh_command
    database       = module.rds.db_endpoint
    s3_frames      = module.s3.frames_bucket_name
    s3_videos      = module.s3.videos_bucket_name
  }
}
