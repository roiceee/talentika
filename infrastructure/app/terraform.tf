terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
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
