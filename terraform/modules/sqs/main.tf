# SQS Queue for AI Processing

# Main AI Analysis Queue
resource "aws_sqs_queue" "ai_analysis" {
  name                       = "${var.project_name}-${var.environment}-ai-analysis"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10       # Long polling
  visibility_timeout_seconds = 300      # 5 minutes (match Lambda timeout)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ai_analysis_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-ai-queue"
    Environment = var.environment
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "ai_analysis_dlq" {
  name                       = "${var.project_name}-${var.environment}-ai-analysis-dlq"
  message_retention_seconds  = 1209600  # 14 days
  receive_wait_time_seconds  = 10

  tags = {
    Name        = "${var.project_name}-ai-dlq"
    Environment = var.environment
  }
}

# CloudWatch Alarm for DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-${var.environment}-dlq-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert when messages appear in DLQ"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.ai_analysis_dlq.name
  }

  tags = {
    Name        = "${var.project_name}-dlq-alarm"
    Environment = var.environment
  }
}
