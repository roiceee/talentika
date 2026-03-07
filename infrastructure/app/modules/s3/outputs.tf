output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.arn
}

output "bucket_region" {
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
  description = "Access Key ID for backend"
  value       = aws_iam_access_key.backend_user_key.id
  sensitive   = true
}

output "backend_secret_access_key" {
  description = "Secret Access Key for backend"
  value       = aws_iam_access_key.backend_user_key.secret
  sensitive   = true
}
