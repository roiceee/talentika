variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "region" {
  description = "DigitalOcean region slug (e.g. sgp1, nyc3)"
  type        = string
  default     = "sgp1"
}

# --- App Platform ---

variable "dockerhub_repository" {
  description = "DockerHub repository name (e.g. talentika-backend)"
  type        = string
  default     = "talentika-backend"
}

variable "app_instance_size" {
  description = "App Platform instance size slug"
  type        = string
  default     = "apps-s-1vcpu-1gb"
}


variable "dockerhub_username" {
  description = "DockerHub username / namespace"
  type        = string
}

variable "dockerhub_token" {
  description = "DockerHub personal access token"
  type        = string
  sensitive   = true
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
