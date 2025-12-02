output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Elastic IP address"
  value       = aws_eip.app.public_ip
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.app.private_ip
}

output "security_group_id" {
  description = "EC2 security group ID"
  value       = aws_security_group.ec2.id
}

output "instance_profile_arn" {
  description = "IAM instance profile ARN"
  value       = aws_iam_instance_profile.ec2.arn
}

output "ssh_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i ${var.project_name}-${var.environment}-key.pem ubuntu@${aws_eip.app.public_ip}"
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "http://${aws_eip.app.public_ip}:3000"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "backend_docs_url" {
  description = "Backend API docs URL"
  value       = "http://${aws_eip.app.public_ip}:8000/docs"
}

output "private_key_path" {
  description = "Path to private key file (if generated)"
  value       = var.key_name == "" ? "${path.root}/${var.project_name}-${var.environment}-key.pem" : "Using existing key: ${var.key_name}"
}
