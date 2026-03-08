# -----------------------------------------------------------------
# DigitalOcean production resources
# App Platform + Managed PostgreSQL + Managed Redis
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

# --- App Platform ---

resource "digitalocean_app" "backend" {
  spec {
    name   = "${var.project_name}-backend"
    region = var.region

    # --- Web service (gunicorn) ---
    service {
      name               = "server"
      instance_count     = 1
      instance_size_slug = var.app_instance_size
      http_port          = 8000

      image {
        registry_type = "DOCKER_HUB"
        registry      = var.dockerhub_username
        repository    = var.dockerhub_repository
        tag           = "latest"
        registry_credentials = "${var.dockerhub_username}:${var.dockerhub_token}"
      }

      health_check {
        http_path            = "/health/"
        initial_delay_seconds = 15
        period_seconds        = 30
      }
    }

    # --- OCR worker ---
    worker {
      name               = "ocr-worker"
      instance_count     = 1
      instance_size_slug = var.app_instance_size
      run_command         = "uv run python manage.py run_analysis_workers --queue ocr"

      image {
        registry_type = "DOCKER_HUB"
        registry      = var.dockerhub_username
        repository    = var.dockerhub_repository
        tag           = "latest"
        registry_credentials = "${var.dockerhub_username}:${var.dockerhub_token}"
      }
    }

    # --- AI analysis worker ---
    worker {
      name               = "ai-analysis-worker"
      instance_count     = 1
      instance_size_slug = var.app_instance_size
      run_command         = "uv run python manage.py run_analysis_workers --queue ai_analysis"

      image {
        registry_type = "DOCKER_HUB"
        registry      = var.dockerhub_username
        repository    = var.dockerhub_repository
        tag           = "latest"
        registry_credentials = "${var.dockerhub_username}:${var.dockerhub_token}"
      }
    }
  }
}

# --- DB firewalls: restrict access to App Platform ---

resource "digitalocean_database_firewall" "postgres_fw" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "app"
    value = digitalocean_app.backend.id
  }
}

resource "digitalocean_database_firewall" "redis_fw" {
  cluster_id = digitalocean_database_cluster.redis.id

  rule {
    type  = "app"
    value = digitalocean_app.backend.id
  }
}
