# --- App Platform ---

output "app_id" {
  description = "ID of the App Platform app (use as DIGITALOCEAN_APP_ID in CI)"
  value       = digitalocean_app.backend.id
}

output "app_default_url" {
  description = "Default URL assigned by App Platform"
  value       = digitalocean_app.backend.default_ingress
}

# --- Postgres ---

output "db_cluster_id" {
  description = "ID of the managed Postgres cluster"
  value       = digitalocean_database_cluster.postgres.id
}

output "db_host" {
  description = "Postgres connection host"
  value       = digitalocean_database_cluster.postgres.host
}

output "db_port" {
  description = "Postgres connection port"
  value       = digitalocean_database_cluster.postgres.port
}

output "db_user" {
  description = "Default Postgres admin user"
  value       = digitalocean_database_cluster.postgres.user
}

output "db_password" {
  description = "Default Postgres admin password"
  value       = digitalocean_database_cluster.postgres.password
  sensitive   = true
}

output "db_uri" {
  description = "Full Postgres connection URI"
  value       = digitalocean_database_cluster.postgres.uri
  sensitive   = true
}

output "db_name" {
  description = "Application database name"
  value       = digitalocean_database_db.app_db.name
}

# --- Redis ---

output "redis_host" {
  description = "Redis connection host"
  value       = digitalocean_database_cluster.redis.host
}

output "redis_port" {
  description = "Redis connection port"
  value       = digitalocean_database_cluster.redis.port
}

output "redis_uri" {
  description = "Full Redis connection URI"
  value       = digitalocean_database_cluster.redis.uri
  sensitive   = true
}
