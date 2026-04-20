# =================================================================
# DigitalOcean App Platform – environment variables for team2
# This file is NOT committed to git. Populate values before applying.
#
# Two-step deploy:
#   Step 1: Apply with placeholder DB/Redis/AWS values below.
#           Terraform will create DB + Redis + S3 + IAM.
#   Step 2: Fill in real values from `terraform output`, then re-apply.
# =================================================================

# --- Docker Hub credentials (same registry, same or new token) ---
dockerhub_registry_credentials = "roiceee:dckr_pat_7O2fI-4em_Ke0Re6AXeUibnRXek"

# --- App environment variables ---
app_env = {
  # Step 2: get from `terraform output db_host` / `terraform output db_uri`
  DB_NAME     = "defaultdb"
  DB_USER     = "doadmin"
  DB_PASSWORD = "AVNS_4x2KgvawX0e0KFileOW"
  DB_HOST     = "talentika-t2-prod-postgres-do-user-36159466-0.h.db.ondigitalocean.com"
  DB_PORT     = 25060

  DEBUG         = "False"
  SECRET_KEY    = "django-insecure-+q^i)fe^yw6d1b^4f$q_2%xq%1nbv&7@a!@o2rf-t5-=8^^*f+"
  ALLOWED_HOSTS = "*"

  DJANGO_SUPERUSER_USERNAME = "admin"
  DJANGO_SUPERUSER_EMAIL    = "admin@talentika.com"
  DJANGO_SUPERUSER_PASSWORD = "admin123"

  EMAIL_HOST          = "smtp.gmail.com"
  EMAIL_PORT          = 587
  EMAIL_USE_TLS       = "True"
  EMAIL_HOST_USER     = "talentikadev@gmail.com"
  EMAIL_HOST_PASSWORD = "afyyiqvcuxqlbmrz"
  DEFAULT_FROM_EMAIL  = "noreply@talentika.com"

  FRONTEND_WEB_URL = "https://talentika.tech"

  # Step 2: get from `terraform output backend_access_key_id` etc.
  STORAGE_BACKEND         = "s3"
  AWS_ACCESS_KEY_ID       = "AKIAVC3OT5JDM34ZXMAG"
  AWS_SECRET_ACCESS_KEY   = "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"
  AWS_STORAGE_BUCKET_NAME = "talentika-prod-bucket"
  AWS_S3_REGION_NAME      = "ap-southeast-1"

  INVITATION_EXPIRY_DAYS = 7

  # Step 2: get from `terraform output redis_uri`
  REDIS_URL = "rediss://default:AVNS_rRjHHTRbobm6V24twM3@talentika-t2-prod-redis-do-user-36159466-0.h.db.ondigitalocean.com:25061"
  REDIS_SSL = "True"

  OPENAI_API_KEY = "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"
  OPENAI_MODEL   = "gpt-4o-mini"
}
