variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "cors_allowed_origins" {
  description = "Origins allowed to access S3 via CORS (for presigned URL uploads)"
  type        = list(string)
  default     = ["*"]
}
