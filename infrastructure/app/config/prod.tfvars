environment  = "prod"
project_name = "talentika"

# CORS: origins allowed to access S3 (for presigned URL uploads)
cors_allowed_origins = [
  "https://talentika.vercel.app", "http://talentika.tech"
]

# --- DigitalOcean region ---

do_region = "sgp1"

# --- Managed Postgres ---

db_size       = "db-s-1vcpu-1gb"
db_node_count = 1
db_version    = "16"
db_name       = "talentika"

# --- Managed Redis ---

redis_size    = "db-s-1vcpu-1gb"
redis_version = "8"

