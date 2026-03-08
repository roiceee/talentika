
# =================================================================
# Root variables
# =================================================================

variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "do_token" {
  description = "DigitalOcean API token. Required for prod; leave empty for dev."
  type        = string
  sensitive   = true
  default     = ""
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "cors_allowed_origins" {
  description = "List of origins allowed to access the S3 bucket via CORS"
  type        = list(string)
  default     = ["*"]
}

# --- Prod-only (DigitalOcean) variables ---

variable "do_region" {
  description = "DigitalOcean region slug. Only used in prod."
  type        = string
  default     = "sgp1"
}

variable "dockerhub_username" {
  description = "DockerHub username / namespace. Only used in prod."
  type        = string
  default     = ""
}

variable "dockerhub_token" {
  description = "DockerHub personal access token. Only used in prod."
  type        = string
  sensitive   = true
  default     = ""
}

variable "dockerhub_repository" {
  description = "DockerHub repository name. Only used in prod."
  type        = string
  default     = "talentika-backend"
}

variable "app_instance_size" {
  description = "App Platform instance size slug. Only used in prod."
  type        = string
  default     = "apps-s-1vcpu-1gb"
}

variable "db_size" {
  description = "Managed Postgres node size slug. Only used in prod."
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_node_count" {
  description = "Number of Postgres cluster nodes. Only used in prod."
  type        = number
  default     = 1
}

variable "db_version" {
  description = "PostgreSQL major version. Only used in prod."
  type        = string
  default     = "16"
}

variable "db_name" {
  description = "Application database name inside the cluster. Only used in prod."
  type        = string
  default     = "talentika"
}

variable "redis_size" {
  description = "Managed Redis node size slug. Only used in prod."
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_version" {
  description = "Redis major version. Only used in prod."
  type        = string
  default     = "7"
}


# =================================================================
# Module: S3 + IAM (both environments)
# =================================================================

module "s3" {
  source = "./modules/s3"

  project_name         = var.project_name
  environment          = var.environment
  cors_allowed_origins = var.cors_allowed_origins
}

# =================================================================
# Module: Prod (Managed Postgres + Redis on DigitalOcean)
# =================================================================

module "prod" {
  source = "./modules/prod"

  count = var.environment == "prod" ? 1 : 0

  project_name         = var.project_name
  region               = var.do_region
  dockerhub_username   = var.dockerhub_username
  dockerhub_token      = var.dockerhub_token
  dockerhub_repository = var.dockerhub_repository
  app_instance_size    = var.app_instance_size
  db_size              = var.db_size
  db_node_count        = var.db_node_count
  db_version           = var.db_version
  db_name              = var.db_name
  redis_size           = var.redis_size
  redis_version        = var.redis_version
}

# =================================================================
# Outputs — S3
# =================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "s3_bucket_region" {
  description = "Region of the S3 bucket"
  value       = module.s3.bucket_region
}

output "iam_policy_arn" {
  description = "ARN of the IAM policy for S3 access"
  value       = module.s3.iam_policy_arn
}

output "backend_user_name" {
  description = "Name of the IAM user for backend"
  value       = module.s3.backend_user_name
}

output "backend_access_key_id" {
  description = "Access Key ID for backend (sensitive)"
  value       = module.s3.backend_access_key_id
  sensitive   = true
}

output "backend_secret_access_key" {
  description = "Secret Access Key for backend (sensitive)"
  value       = module.s3.backend_secret_access_key
  sensitive   = true
}

# =================================================================
# Outputs — Prod (null in dev)
# =================================================================

output "app_id" {
  description = "Prod App Platform app ID — use as DIGITALOCEAN_APP_ID in CI (null in dev)"
  value       = try(module.prod[0].app_id, null)
}

output "app_default_url" {
  description = "Prod App Platform default URL (null in dev)"
  value       = try(module.prod[0].app_default_url, null)
}

output "db_host" {
  description = "Prod Postgres host (null in dev)"
  value       = try(module.prod[0].db_host, null)
}

output "db_port" {
  description = "Prod Postgres port (null in dev)"
  value       = try(module.prod[0].db_port, null)
}

output "db_uri" {
  description = "Prod Postgres connection URI (null in dev)"
  value       = try(module.prod[0].db_uri, null)
  sensitive   = true
}

output "redis_host" {
  description = "Prod Redis host (null in dev)"
  value       = try(module.prod[0].redis_host, null)
}

output "redis_uri" {
  description = "Prod Redis connection URI (null in dev)"
  value       = try(module.prod[0].redis_uri, null)
  sensitive   = true
}