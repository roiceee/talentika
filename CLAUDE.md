# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commits

- Commit per feature — one logical change per commit
- No co-author signatures in commit messages

## Project Overview

**Talentika** is a multi-tenant HR SaaS platform where organizations post job profiles, collect applications, and run AI-powered resume screening. It is a decision-support tool — final hiring decisions remain with HR.

```
backend/        → Django 6 REST API (Python 3.13+, uv)
frontend/       → Next.js 16 BFF + UI (pnpm, TypeScript, Tailwind)
infrastructure/ → Terraform (AWS S3, IAM)
```

## Commands

### Backend (run from `backend/`)

```bash
./dev.sh                                          # start Docker DB → migrate → run Django :8000
uv run python manage.py runserver                 # Django dev server
uv run python manage.py makemigrations && uv run python manage.py migrate
uv run python manage.py test <app>.<tests>.<file> # run a single test module
uv run python manage.py seed_job_data             # seed JobCategory, ExperienceLevel, AIScreeningConfiguration
uv run python manage.py createsuperuser
uv run python manage.py rqworker ocr_queue        # OCR worker
uv run python manage.py rqworker ai_queue         # AI analysis worker
uv run python manage.py rqworker export_queue     # export worker
docker compose up -d                              # start PostgreSQL + Redis only
docker compose down -v                            # reset volumes
```

### Frontend (run from `frontend/`)

```bash
pnpm dev           # dev server on :3000
pnpm build
pnpm openapi-ts    # regenerate src/lib/client/ from backend /swagger.json (reads BACKEND_URL env)
```

## Architecture

### Request Flow

```
Browser → Next.js BFF routes (/api/*) → Django REST API (:8000) → PostgreSQL (:5438)
                                                                 ↘ Redis → RQ Workers
```

- Frontend **never** calls Django directly. All API calls go through BFF routes in `frontend/src/app/api/`.
- BFF routes validate CSRF (cookie vs `x-csrf-token` header), inject JWT via `authenticatedSdkCall()`, and format errors via `errorResponse()`.
- CSRF exempt: `/api/auth/csrf`, `/api/auth/refresh`.

### Analysis Pipeline (async, RQ-based)

Application submitted → OCR job enqueued → `ocr_queue` worker extracts text via **Tesseract OCR** (pytesseract + pdf2image) → `ai_queue` worker sends to LLM → structured output validated via Pydantic → saved to DB.

Status machine: `UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE / FAILED`

AI uses OpenAI (default model: `gpt-4o-mini`, configurable via `OPENAI_MODEL` env).

### Django Apps

| App | Purpose |
|-----|---------|
| `users/` | Custom User (email auth, UUID PK), password reset |
| `organizations/` | Org management, memberships (ORG_ADMIN/MEMBER), email invitations |
| `job_profile/` | JobProfile, Question, JobCategory, ExperienceLevel, AIScreeningConfiguration |
| `job_applications/` | Application submission, file uploads, status workflow, export jobs |
| `job_application_analysis/` | RQ pipeline: OCR → AI scoring |
| `geo/` | Country/state/city lookup (public endpoints) |
| `health/` | `/health` liveness check |

## Critical Conventions

### URLs — Trailing Slashes Required
`APPEND_SLASH = False`. Missing slash → 404 (no redirect).
- ✅ `GET /api/organizations/`  ❌ `GET /api/organizations`

Multiple Django apps share `/api/` prefix — see `backend/app/urls.py`.

### Backend View Pattern

```python
@swagger_auto_schema(method='post', tags=['JobProfiles'], request_body=..., responses={...})
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizationAdmin])
def create_job_profile(request, org_id): ...
```

Always function-based views. Always include `@swagger_auto_schema`. URL names in kebab-case. UUID path converters: `<uuid:org_id>`.

### Custom Permissions (`organizations/permissions.py`)

`IsOrganizationAdmin`, `IsOrganizationMember`, `IsApprovedOrganization`, `IsSuperAdmin`, `IsOrgAdminOfOwnOrganization`

### Frontend API Client

`src/lib/client/` is **auto-generated** — never edit manually. Regenerate with `pnpm openapi-ts` after backend changes.

### Storage

`STORAGE_BACKEND=local` (dev) or `STORAGE_BACKEND=s3` (prod). File download logic in `workers.py` branches on this.

### Duplicate Detection

Applications deduplicated using weighted composite score: Name 40% (RapidFuzz), Phone 35%, Email 20%, SHA-256 file hash 25%. Threshold: 0.75.

## Adding a New Django App

1. `uv run python manage.py startapp <name>`
2. Add to `INSTALLED_APPS` in `backend/app/settings.py`
3. Create `urls.py`, include in `backend/app/urls.py`
4. Use modular structure: `<app>/models/`, `<app>/views/`, `<app>/serializers/`, `<app>/tests/`

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/urls.py` | Full URL routing |
| `backend/app/settings.py` | All config (JWT, email, Redis, AI provider) |
| `backend/organizations/permissions.py` | Custom DRF permissions |
| `backend/job_application_analysis/workers.py` | RQ worker pipeline logic |
| `backend/job_application_analysis/ai_service.py` | OpenAI AI backend |
| `backend/docker-compose.yml` | PostgreSQL (port 5438) + Redis + workers |
| `frontend/src/proxy.ts` | CSRF edge middleware |
| `frontend/src/lib/hey-api.ts` | Axios client config |
| `frontend/src/app/api/` | BFF route handlers |

## API Docs (local)

- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc
