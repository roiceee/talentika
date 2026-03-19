variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vercel_team_id" {
  description = "Vercel team ID (leave empty for personal accounts)"
  type        = string
  default     = ""
}

variable "frontend_domain" {
  description = "Custom domain for the frontend (e.g. talentika.tech)"
  type        = string
  default     = ""
}

variable "backend_url" {
  description = "Backend API URL (set as BACKEND_URL env var on Vercel)"
  type        = string
  sensitive   = true
}

variable "framework" {
  description = "Framework preset for Vercel"
  type        = string
  default     = "nextjs"
}
