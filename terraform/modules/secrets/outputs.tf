output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "secrets_name" {
  description = "Secrets Manager name"
  value       = aws_secretsmanager_secret.app_secrets.name
}
