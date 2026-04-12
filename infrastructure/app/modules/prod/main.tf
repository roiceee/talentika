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

# =================================================================
# DigitalOcean App Platform – Backend
# =================================================================

resource "digitalocean_app" "talentika-backend" {
  spec {
    name   = "${var.project_name}-backend"
    region = "sgp"

    features = ["buildpack-stack=ubuntu-22"]

    # ── Custom domain ──
    domain {
      name = var.app_domain
      type = "PRIMARY"
    }

    # ── App-wide environment variables ──
    dynamic "env" {
      for_each = var.app_env
      content {
        key   = env.key
        value = env.value
        scope = "RUN_AND_BUILD_TIME"
        type  = "SECRET"
      }
    }

    # ── Web service ──
    service {
      name               = "server"
      instance_count     = var.app_instance_count
      instance_size_slug = var.app_instance_size
      http_port          = 8000

      image {
        registry_type        = "DOCKER_HUB"
        registry             = var.dockerhub_registry
        repository           = var.dockerhub_image_repo
        tag                  = var.dockerhub_image_tag
        registry_credentials = var.dockerhub_registry_credentials
      }

      health_check {
        http_path             = "/health/"
        initial_delay_seconds = 15
        period_seconds        = 30
      }
    }

    # ── OCR worker ──
    worker {
      name               = "ocr-worker"
      instance_count     = 1
      instance_size_slug = var.app_instance_size
      run_command        = "uv run python manage.py run_analysis_workers --queue ocr_queue --concurrency 4"

      image {
        registry_type        = "DOCKER_HUB"
        registry             = var.dockerhub_registry
        repository           = var.dockerhub_image_repo
        tag                  = var.dockerhub_image_tag
        registry_credentials = var.dockerhub_registry_credentials
      }
    }

    # ── AI analysis worker ──
    worker {
      name               = "ai-analysis-worker"
      instance_count     = 3
      instance_size_slug = var.app_instance_size
      run_command        = "uv run python manage.py run_analysis_workers --queue ai_queue --concurrency 10"

      image {
        registry_type        = "DOCKER_HUB"
        registry             = var.dockerhub_registry
        repository           = var.dockerhub_image_repo
        tag                  = var.dockerhub_image_tag
        registry_credentials = var.dockerhub_registry_credentials
      }
    }

    # ── Export worker ──
    worker {
      name               = "export-worker"
      instance_count     = 1
      instance_size_slug = var.app_instance_size
      run_command        = "uv run python manage.py run_analysis_workers --queue export_queue"

      image {
        registry_type        = "DOCKER_HUB"
        registry             = var.dockerhub_registry
        repository           = var.dockerhub_image_repo
        tag                  = var.dockerhub_image_tag
        registry_credentials = var.dockerhub_registry_credentials
      }
    }

    # ── Ingress routing ──
    ingress {
      rule {
        component {
          name = "server"
        }
        match {
          path {
            prefix = "/"
          }
        }
      }
    }
  }
}

