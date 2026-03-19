output "project_id" {
  description = "Vercel project ID"
  value       = vercel_project.frontend.id
}

output "deployment_url" {
  description = "Default Vercel deployment URL"
  value       = "https://${vercel_project.frontend.name}.vercel.app"
}
