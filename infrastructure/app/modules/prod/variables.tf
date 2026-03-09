variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "region" {
  description = "DigitalOcean region slug (e.g. sgp1, nyc3)"
  type        = string
  default     = "sgp1"
}

# --- Managed Postgres ---

variable "db_size" {
  description = "Postgres cluster node size slug"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_node_count" {
  description = "Number of Postgres cluster nodes"
  type        = number
  default     = 1
}

variable "db_version" {
  description = "PostgreSQL major version"
  type        = string
  default     = "16"
}

variable "db_name" {
  description = "Name of the application database to create inside the cluster"
  type        = string
  default     = "talentika"
}

# --- Managed Redis ---

variable "redis_size" {
  description = "Redis cluster node size slug"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_version" {
  description = "Redis major version"
  type        = string
  default     = "8"
}

# --- App Platform ---

variable "app_env" {
  description = "Map of environment variables for the app"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "dockerhub_registry_credentials" {
  description = "Docker Hub credentials (username:token)"
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
  description = "Docker Hub image repository name"
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
