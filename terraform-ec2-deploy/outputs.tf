# Simplified Outputs

output "ec2_public_ip" {
  description = "EC2 Elastic IP"
  value       = aws_eip.app.public_ip
}

output "ec2_instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.app.id
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
  description = "Backend API docs"
  value       = "http://${aws_eip.app.public_ip}:8000/docs"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ${local_file.ssh_key.filename} ubuntu@${aws_eip.app.public_ip}"
}

output "vpc_id" {
  description = "VPC ID (default)"
  value       = data.aws_vpc.default.id
}

output "subnet_id" {
  description = "Subnet ID used"
  value       = data.aws_subnets.default.ids[0]
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.app.id
}

output "ssh_key_path" {
  description = "SSH private key path"
  value       = local_file.ssh_key.filename
}
