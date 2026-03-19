
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
  db_size              = var.db_size
  db_node_count        = var.db_node_count
  db_version           = var.db_version
  db_name              = var.db_name
  redis_size           = var.redis_size
  redis_version        = var.redis_version

  # App Platform
  app_env                        = var.app_env
  dockerhub_registry_credentials = var.dockerhub_registry_credentials
  app_domain                     = var.app_domain
  app_instance_size              = var.app_instance_size
  app_instance_count             = var.app_instance_count
  dockerhub_image_repo           = var.dockerhub_image_repo
  dockerhub_image_tag            = var.dockerhub_image_tag
  dockerhub_registry             = var.dockerhub_registry
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


# =================================================================
# App-level variables (passed through to prod module)
# =================================================================

variable "app_env" {
  description = "Map of environment variables for the DigitalOcean App Platform app"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "dockerhub_registry_credentials" {
  description = "Docker Hub credentials in the format username:token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "app_domain" {
  description = "Custom domain for the backend app"
  type        = string
  default     = "api.talentika.tech"
}

variable "app_instance_size" {
  description = "Instance size slug for all app components"
  type        = string
  default     = "apps-s-1vcpu-1gb"
}

variable "app_instance_count" {
  description = "Number of instances for the web service"
  type        = number
  default     = 1
}

variable "dockerhub_image_repo" {
  description = "Docker Hub repository (owner/repo format without tag)"
  type        = string
  default     = "talentika-backend"
}

variable "dockerhub_image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "dockerhub_registry" {
  description = "Docker Hub registry (username)"
  type        = string
  default     = "roiceee"
}

# =================================================================
# Module: Vercel (frontend — both environments)
# =================================================================

module "vercel" {
  source = "./modules/vercel"

  project_name    = var.project_name
  backend_url     = var.vercel_backend_url
  frontend_domain = var.vercel_frontend_domain
  vercel_team_id  = var.vercel_team_id
}

# =================================================================
# Outputs — App (null in dev)
# =================================================================

output "app_live_url" {
  description = "Live URL of the backend app (null in dev)"
  value       = try(module.prod[0].app_live_url, null)
}

output "app_default_ingress" {
  description = "Default ingress URL of the backend app (null in dev)"
  value       = try(module.prod[0].app_default_ingress, null)
}

# =================================================================
# Vercel variables
# =================================================================

variable "vercel_api_token" {
  description = "Vercel API token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vercel_team_id" {
  description = "Vercel team ID (leave empty for personal accounts)"
  type        = string
  default     = ""
}

variable "vercel_backend_url" {
  description = "Backend API URL to inject as BACKEND_URL on Vercel"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vercel_frontend_domain" {
  description = "Custom domain for the Vercel frontend (e.g. talentika.tech)"
  type        = string
  default     = ""
}

# =================================================================
# Outputs — Vercel
# =================================================================

output "vercel_project_id" {
  description = "Vercel project ID"
  value       = module.vercel.project_id
}

output "vercel_deployment_url" {
  description = "Default Vercel deployment URL"
  value       = module.vercel.deployment_url
}