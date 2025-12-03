output "frames_bucket_name" {
  description = "Frames bucket name"
  value       = aws_s3_bucket.frames.id
}

output "frames_bucket_arn" {
  description = "Frames bucket ARN"
  value       = aws_s3_bucket.frames.arn
}

output "videos_bucket_name" {
  description = "Videos bucket name"
  value       = aws_s3_bucket.videos.id
}

output "videos_bucket_arn" {
  description = "Videos bucket ARN"
  value       = aws_s3_bucket.videos.arn
}

output "static_bucket_name" {
  description = "Static files bucket name"
  value       = aws_s3_bucket.static.id
}

output "static_bucket_arn" {
  description = "Static files bucket ARN"
  value       = aws_s3_bucket.static.arn
}
