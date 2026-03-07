# -----------------------------------------------------------------
# DigitalOcean production resources
# Droplet + Managed PostgreSQL + Managed Redis
# -----------------------------------------------------------------

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# --- SSH Key ---

data "digitalocean_ssh_key" "default" {
  name = var.ssh_key_name
}

# --- Droplet ---

resource "digitalocean_droplet" "app" {
  name     = "${var.project_name}-prod"
  region   = var.region
  size     = var.droplet_size
  image    = var.droplet_image
  ssh_keys = [data.digitalocean_ssh_key.default.id]

  tags = [var.project_name, "prod"]
}

# --- Firewall for Droplet ---

resource "digitalocean_firewall" "app" {
  name        = "${var.project_name}-prod-fw"
  droplet_ids = [digitalocean_droplet.app.id]

  # SSH
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTP
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # All outbound
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
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

# --- DB firewalls: restrict access to the Droplet only ---

resource "digitalocean_database_firewall" "postgres_fw" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.app.id
  }
}

resource "digitalocean_database_firewall" "redis_fw" {
  cluster_id = digitalocean_database_cluster.redis.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.app.id
  }
}
