terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }

  # Backend is configured per environment via -backend-config flag:
  #   dev:  terraform init -backend-config=backend-dev.hcl
  #   prod: terraform init -backend-config=backend-prod.hcl
  backend "s3" {}
}

provider "aws" {
  region = "ap-southeast-1"
}

provider "digitalocean" {
  # Token is only set in prod (config/prod.tfvars).
  # Leave empty in dev — the provider won't authenticate unless DO resources are used.
  token = var.do_token
}

provider "vercel" {
  # Set VERCEL_API_TOKEN env var or pass via vercel_api_token variable.
  api_token = var.vercel_api_token
}
