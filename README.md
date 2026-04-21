# Talentika

Talentika is a multi-tenant HR decision-support platform. Organizations post job profiles, share public application links with candidates, and let the system run AI-powered resume screening in the background. HR professionals review structured AI insights alongside raw applications — the final hiring decision always stays with the team.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Django REST Framework, Python 3.13+ |
| Frontend | Next.js 16 (BFF + UI), TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 |
| Queue / Workers | Redis + RQ |
| OCR | Tesseract 4 (pytesseract + pdf2image) |
| AI | OpenAI GPT (structured outputs via Pydantic) |
| Storage | AWS S3 |
| Infrastructure | Terraform (AWS S3/IAM, DigitalOcean App Platform) |

## Architecture

```
Browser → Next.js BFF (/api/*) → Django REST API (:8000) → PostgreSQL
                                                          ↘ Redis → RQ Workers
```

- The frontend never calls Django directly. All requests go through BFF routes in `frontend/src/app/api/`.
- BFF routes handle CSRF validation and JWT injection via `authenticatedSdkCall()`.

### Analysis Pipeline

```
Application submitted
        │
        ▼
  [ocr_queue]   OCR: pdf2image + Tesseract extract resume text
        │
        ▼
  [ai_queue]    AI: resume text + job profile context → OpenAI structured output
        │
        ▼
  Result saved (available for HR review)
```

Status machine: `UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE / FAILED`

## Prerequisites

- Python 3.13+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv)
- pnpm
- Docker + Docker Compose
- Terraform
- Tesseract OCR
- LibreOffice (DOCX → PDF conversion)
- AWS account with IAM and S3 permissions
- OpenAI API key

## Setup

### 1. Clone

```bash
git clone https://github.com/roiceee/talentika.git
cd talentika
```

### 2. Provision Infrastructure (S3)

The system uses AWS S3 as the storage backend. Terraform provisions the S3 bucket and the IAM user the backend authenticates as.

```bash
cd infrastructure/app
terraform init -backend-config=backend-dev.hcl
terraform apply -var-file=config/dev.tfvars
```

Retrieve the generated credentials after apply:

```bash
terraform output -raw backend_access_key_id
terraform output -raw backend_secret_access_key
terraform output s3_bucket_name        # talentika-dev-bucket
```

### 3. Backend

Navigate to `backend/` and create a `.env` file:

```env
SECRET_KEY=<secure-random-string>

# Database (Docker default)
DATABASE_URL=postgresql://talentika_user:talentika_password@localhost:5438/talentika_dev

# Redis (Docker default)
REDIS_URL=redis://localhost:6379/0

# AWS S3 (from Terraform output)
STORAGE_BACKEND=s3
AWS_STORAGE_BUCKET_NAME=talentika-dev-bucket
AWS_S3_REGION_NAME=ap-southeast-1
AWS_ACCESS_KEY_ID=<from terraform output>
AWS_SECRET_ACCESS_KEY=<from terraform output>

# OpenAI
OPENAI_API_KEY=<your-key>
OPENAI_MODEL=gpt-4o-mini

# Email (optional for dev — invitation and confirmation emails)
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
FRONTEND_WEB_URL=http://localhost:3000
```

Start services:

```bash
docker compose up -d                                  # PostgreSQL + Redis
./dev.sh                                              # migrate + start Django on :8000
uv run python manage.py seed_job_data                 # seed reference data
uv run python manage.py rqworker ocr_queue            # OCR worker (separate terminal)
uv run python manage.py rqworker ai_queue             # AI worker (separate terminal)
uv run python manage.py rqworker export_queue         # export worker (separate terminal)
```

Create a superuser:

```bash
uv run python manage.py createsuperuser
```

### 4. Frontend

Navigate to `frontend/` and create a `.env.local` file:

```env
BACKEND_URL=http://localhost:8000
```

Install and run:

```bash
pnpm install
pnpm dev    # :3000
```

## Development Commands

### Backend (`backend/`)

```bash
./dev.sh                                                      # start everything
uv run python manage.py runserver                             # Django only
uv run python manage.py makemigrations && uv run python manage.py migrate
uv run python manage.py test <app>.<tests>.<file>             # run a test module
uv run python manage.py seed_job_data                         # seed reference data
docker compose down -v                                        # reset DB + Redis volumes
```

### Frontend (`frontend/`)

```bash
pnpm dev           # dev server
pnpm build         # production build
pnpm openapi-ts    # regenerate src/lib/client/ from backend /swagger.json
```

## API Docs

With the backend running:

- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/        Django REST API
frontend/       Next.js BFF + UI
infrastructure/ Terraform (AWS S3/IAM + DigitalOcean prod)
```

### Django Apps

| App | Purpose |
|---|---|
| `users/` | Custom User (email auth, UUID PK), password reset |
| `organizations/` | Org management, memberships, email invitations |
| `job_profile/` | JobProfile, Questions, Categories, AI screening config |
| `job_applications/` | Submission, file uploads, status workflow, duplicate detection, export |
| `job_application_analysis/` | RQ pipeline: OCR → AI scoring |
| `geo/` | Country/state/city lookup |
| `health/` | `/health` liveness check |

## Infrastructure

Terraform state is stored remotely in S3 (`talentika-terraform-state`, `ap-southeast-1`). Dev and prod use separate state files via `-backend-config`.

```bash
# Switch to prod
terraform init -backend-config=backend-prod.hcl -reconfigure
terraform apply -var-file=config/prod.tfvars
```

Prod additionally provisions managed PostgreSQL and Redis on DigitalOcean App Platform.
