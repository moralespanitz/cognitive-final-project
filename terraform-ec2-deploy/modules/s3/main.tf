# S3 Buckets for Frames, Videos, and Static Files

# Frames Bucket (Short retention - 7 days)
resource "aws_s3_bucket" "frames" {
  bucket = "${var.project_name}-${var.environment}-frames"

  tags = {
    Name        = "${var.project_name}-frames"
    Environment = var.environment
    Purpose     = "ESP32 camera frames"
  }
}

resource "aws_s3_bucket_versioning" "frames" {
  bucket = aws_s3_bucket.frames.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "frames" {
  bucket = aws_s3_bucket.frames.id

  rule {
    id     = "delete-old-frames"
    status = "Enabled"

    expiration {
      days = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

resource "aws_s3_bucket_notification" "frames" {
  count = var.frame_processor_lambda_arn != null ? 1 : 0

  bucket = aws_s3_bucket.frames.id

  lambda_function {
    lambda_function_arn = var.frame_processor_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".jpg"
  }

  depends_on = var.lambda_s3_permission != null ? [var.lambda_s3_permission] : []
}

# Videos Bucket (Long retention with Glacier transition)
resource "aws_s3_bucket" "videos" {
  bucket = "${var.project_name}-${var.environment}-videos"

  tags = {
    Name        = "${var.project_name}-videos"
    Environment = var.environment
    Purpose     = "Video archives"
  }
}

resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "archive-to-glacier"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 180
    }
  }
}

# Static Files Bucket (Frontend assets, reports, etc.)
resource "aws_s3_bucket" "static" {
  bucket = "${var.project_name}-${var.environment}-static"

  tags = {
    Name        = "${var.project_name}-static"
    Environment = var.environment
    Purpose     = "Static files and reports"
  }
}

resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access for all buckets
resource "aws_s3_bucket_public_access_block" "frames" {
  bucket = aws_s3_bucket.frames.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket = aws_s3_bucket.videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "frames" {
  bucket = aws_s3_bucket.frames.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
