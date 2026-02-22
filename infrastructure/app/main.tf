
# Variables for environment
variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "cors_allowed_origins" {
  description = "List of origins allowed to access the S3 bucket via CORS (e.g. your frontend URL)"
  type        = list(string)
  default     = ["*"]
}

# S3 Bucket for application storage
resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.project_name}-${var.environment}-bucket"

  tags = {
    Name        = "${var.project_name}-${var.environment}-bucket"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Enable versioning (recommended for backup/recovery)
resource "aws_s3_bucket_versioning" "app_bucket_versioning" {
  bucket = aws_s3_bucket.app_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access (security best practice)
resource "aws_s3_bucket_public_access_block" "app_bucket_public_access" {
  bucket = aws_s3_bucket.app_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_bucket_encryption" {
  bucket = aws_s3_bucket.app_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CORS configuration (required for presigned URL uploads from the browser)
resource "aws_s3_bucket_cors_configuration" "app_bucket_cors" {
  bucket = aws_s3_bucket.app_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "app_bucket_lifecycle" {
  bucket = aws_s3_bucket.app_bucket.id
  rule {
    id     = "delete-temp-files"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 1
    }
  }
  rule {
    id     = "transition-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# IAM Policy for backend application access
resource "aws_iam_policy" "s3_backend_access" {
  name        = "${var.project_name}-${var.environment}-backend-s3-access"
  description = "Policy for backend application to access S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:HeadBucket"
        ]
        Resource = [
          aws_s3_bucket.app_bucket.arn,
          "${aws_s3_bucket.app_bucket.arn}/*"
        ]
      }
    ]
  })
}

# IAM User for backend application (alternative to IAM role)
resource "aws_iam_user" "backend_user" {
  name = "${var.project_name}-${var.environment}-backend-user"

  tags = {
    Name        = "${var.project_name}-${var.environment}-backend-user"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach policy to user
resource "aws_iam_user_policy_attachment" "backend_s3_policy_attachment" {
  user       = aws_iam_user.backend_user.name
  policy_arn = aws_iam_policy.s3_backend_access.arn
}

# Create access key for backend user
resource "aws_iam_access_key" "backend_user_key" {
  user = aws_iam_user.backend_user.name
}

# Outputs for your application to use
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.arn
}

output "s3_bucket_region" {
  description = "Region of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.region
}

output "iam_policy_arn" {
  description = "ARN of the IAM policy for S3 access"
  value       = aws_iam_policy.s3_backend_access.arn
}

output "backend_user_name" {
  description = "Name of the IAM user for backend"
  value       = aws_iam_user.backend_user.name
}

output "backend_access_key_id" {
  description = "Access Key ID for backend (sensitive)"
  value       = aws_iam_access_key.backend_user_key.id
  sensitive   = true
}

output "backend_secret_access_key" {
  description = "Secret Access Key for backend (sensitive)"
  value       = aws_iam_access_key.backend_user_key.secret
  sensitive   = true
}