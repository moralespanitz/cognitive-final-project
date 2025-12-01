variable "project_name" {
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
