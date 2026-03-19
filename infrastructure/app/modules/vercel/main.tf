# -----------------------------------------------------------------
# Import existing Vercel project
# Run `terraform import` or use this block (Terraform >= 1.5).
# Replace VERCEL_PROJECT_ID with the ID from your Vercel dashboard
# (Project Settings → General → Project ID).
# -----------------------------------------------------------------

import {
  to = vercel_project.frontend
  id = "VERCEL_PROJECT_ID"
}

terraform {
  required_providers {
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }
}

# -----------------------------------------------------------------
# Vercel project
# -----------------------------------------------------------------

resource "vercel_project" "frontend" {
  name      = "${var.project_name}-frontend"
  framework = var.framework

  git_repository = {
    type              = "github"
    repo              = "roiceee/talentika"
    production_branch = "main"
  }

  root_directory             = "frontend"
  ignore_command             = "git diff HEAD^ HEAD --quiet -- frontend/"
  serverless_function_region = "sin1"
}

# -----------------------------------------------------------------
# Environment variables
# -----------------------------------------------------------------

resource "vercel_project_environment_variable" "backend_url" {
  project_id = vercel_project.frontend.id
  key        = "BACKEND_URL"
  value      = var.backend_url
  target     = ["production", "preview"]
  sensitive  = true
}

# -----------------------------------------------------------------
# Custom domain (optional)
# -----------------------------------------------------------------

resource "vercel_project_domain" "custom" {
  count      = var.frontend_domain != "" ? 1 : 0
  project_id = vercel_project.frontend.id
  domain     = var.frontend_domain
}
