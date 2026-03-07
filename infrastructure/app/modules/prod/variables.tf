variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "region" {
  description = "DigitalOcean region slug (e.g. sgp1, nyc3)"
  type        = string
  default     = "sgp1"
}

# --- Droplet ---

variable "ssh_key_name" {
  description = "Name of the SSH key registered in your DigitalOcean account"
  type        = string
}

variable "droplet_size" {
  description = "Droplet size slug (e.g. s-1vcpu-1gb, s-2vcpu-2gb)"
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "droplet_image" {
  description = "Droplet OS image slug"
  type        = string
  default     = "ubuntu-24-04-x64"
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
