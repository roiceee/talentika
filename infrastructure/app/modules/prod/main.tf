# -----------------------------------------------------------------
# DigitalOcean production resources
# Managed PostgreSQL + Managed Redis
# -----------------------------------------------------------------

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# --- Managed PostgreSQL cluster ---

resource "digitalocean_database_cluster" "postgres" {
  name       = "${var.project_name}-prod-postgres"
  engine     = "pg"
  version    = var.db_version
  size       = var.db_size
  region     = var.region
  node_count = var.db_node_count

  tags = [var.project_name, "prod"]
}

resource "digitalocean_database_db" "app_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_name
}

# --- Managed Redis ---

resource "digitalocean_database_cluster" "redis" {
  name       = "${var.project_name}-prod-redis"
  engine     = "valkey"
  version    = var.redis_version
  size       = var.redis_size
  region     = var.region
  node_count = 1

  tags = [var.project_name, "prod"]
}


