output "ai_queue_url" {
  description = "AI analysis queue URL"
  value       = aws_sqs_queue.ai_analysis.url
}

output "ai_queue_arn" {
  description = "AI analysis queue ARN"
  value       = aws_sqs_queue.ai_analysis.arn
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = aws_sqs_queue.ai_analysis_dlq.url
}

output "dlq_arn" {
  description = "Dead letter queue ARN"
  value       = aws_sqs_queue.ai_analysis_dlq.arn
}
