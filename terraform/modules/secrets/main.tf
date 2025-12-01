# AWS Secrets Manager for Sensitive Configuration

resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-${var.environment}-secrets"
  description = "Application secrets for TaxiWatch"

  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-secrets"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    SECRET_KEY     = var.secret_key
    OPENAI_API_KEY = var.openai_api_key
    DB_PASSWORD    = var.db_password
  })
}
