# Talentika - AI Coding Agent Instructions

## Architecture Overview

Full-stack SaaS platform for organizations to post job profiles, collect applications, and run AI-powered resume screening.

```
backend/   → Django 6 REST API (Python 3.13+, uv)
frontend/  → Next.js 16 app (pnpm, TypeScript)
```

**Django Apps:**

- `users/` — custom User model (email auth), profile, password reset
- `organizations/` — org management, memberships, email invitations
- `job_profile/` — job profiles, Q&A questions, job categories, AI screening configs
- `job_applications/` — application submission, file uploads, status workflow
- `job_application_analysis/` — RQ-based pipeline: OCR (doctr) → AI scoring (OpenAI/Gemini)
- `health/` — `/health` liveness check

## Backend Developer Workflow

**Start everything:** `./backend/dev.sh` (starts Docker PostgreSQL → runs migrations → starts Django on :8000)

**All Python commands use `uv` (run from `backend/`):**

```bash
uv run python manage.py makemigrations && uv run python manage.py migrate
uv run python manage.py test organizations.tests.test_invitations
uv run python manage.py test users.tests.test_password_reset
uv run python manage.py seed_job_data   # seeds JobCategory, ExperienceLevel, AIScreeningConfiguration
uv run python manage.py createsuperuser
```

**Database:** PostgreSQL 16 in Docker on port **5438** (not 5432). Name: `talentika_dev`, user: `talentika_user`.

- Start only DB: `docker compose up -d` (from `backend/`)
- Reset: `docker compose down -v`

**Background workers (RQ, not Celery):**

```bash
uv run python manage.py rqworker ocr_queue    # OCR pipeline
uv run python manage.py rqworker ai_queue     # AI analysis pipeline
```

`REDIS_URL` env var (default `redis://localhost:6379/0`). Pipeline: `ocr_queue` → upon completion → enqueues `ai_queue`.

## Frontend Developer Workflow

```bash
cd frontend
pnpm dev                # dev server on :3000
pnpm build
pnpm openapi-ts         # regenerate src/lib/client/ from backend /swagger.json
```

`src/lib/client/` is **auto-generated** from the backend's OpenAPI spec — never edit those files manually. Generation reads `BACKEND_URL` env var.

## Critical Conventions

**`APPEND_SLASH = False`** — URL patterns must include trailing slash; requests without it get 404:

- ✅ `GET /api/organizations/` ❌ `GET /api/organizations`

**Multiple apps share `/api/` prefix** (see [backend/app/urls.py](backend/app/urls.py)):

```python
path("api/users/", include("users.urls"))
path("api/",       include("organizations.urls"))
path("api/",       include("job_profile.urls"))
path("api/",       include("job_applications.urls"))
path("api/",       include("job_application_analysis.urls"))
```

**Modular app structure** — use subdirectories, not flat files:

```
app/models/     app/views/     app/serializers/     app/tests/
```

**API views pattern** — always function-based + Swagger decorator + tags:

```python
@swagger_auto_schema(method='post', tags=['JobProfiles'], request_body=..., responses={...})
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizationAdmin])
def create_job_profile(request, org_id): ...
```

**Custom permissions** (see [backend/organizations/permissions.py](backend/organizations/permissions.py)):

- `IsOrganizationAdmin` / `IsOrganizationMember` — read `org_id` from URL kwargs
- `IsOrgAdminOfOwnOrganization` — stricter check for mutations

**Frontend CSRF:** Edge middleware ([frontend/src/proxy.ts](frontend/src/proxy.ts)) validates CSRF cookie vs `x-csrf-token` header for all mutating BFF routes (`/api/*`). Exempt: `/api/auth/csrf`, `/api/auth/refresh`.

**Frontend API calls** go through Next.js BFF routes (`frontend/src/app/api/`) proxying to Django — never call Django directly from the browser.

## Key Data Flows

**Application submission:**
`POST /api/applications/submit/` → creates `JobApplication` + `QuestionAnswer` records → `_trigger_analysis_pipeline()` (silent fail) → enqueues OCR via RQ.

**Resume pre-upload:**
`POST /api/applications/submit/upload/resume/` → `TemporaryFileUpload` (returns UUID) → pass UUID in submission payload. Dedup via SHA-256.

**Analysis pipeline state machine:** `UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE / FAILED`
OCR uses **doctr** (singleton, lazy-loaded). AI provider via `AI_PROVIDER` env (`openai` or `gemini`); models via `OPENAI_MODEL` / `GEMINI_MODEL`.

**Invitation flow:**

1. Org admin: `POST /api/organizations/{org_id}/invitations/` → email with 7-day token
2. New users: register with token → auto-join. Existing users: `POST /api/invitations/accept/`

**Password reset:** `POST /api/users/password-reset/` → email → `POST /api/users/password-reset/confirm/` with token (24h, single-use, `used_at` field).

## Auth

Email-based JWT. `POST /api/users/auth/login/` with `{"email", "password"}` → `access` (1h) + `refresh` (7d).
Header: `Authorization: Bearer <token>`. Serializer: `EmailTokenObtainPairSerializer` in [backend/users/authentication.py](backend/users/authentication.py).

## Domain Models

**`job_profile`:** `JobProfile` (FK→Organization, title, category, employment_type, experience_level, requirements ArrayField, skills JSONField `[{skill, is_required}]`, optional AI screening config, `is_active`), `Question` (text/mcq/mcq_single), lookup tables `JobCategory` / `ExperienceLevel` / `AIScreeningConfiguration`.

**`job_applications`:** `JobApplication` (FK→JobProfile, status: submitted→under_review→shortlisted→rejected), `QuestionAnswer`, `ApplicationAttachment` (S3/local storage), `TemporaryFileUpload`.

**`organizations`:** `Organization` (status: PENDING/APPROVED/REJECTED/SUSPENDED; auto-approved via API), `OrganizationMembership` (ORG_ADMIN/MEMBER), `OrganizationInvitation`, `Address`.

**`users`:** `User` (AbstractUser, UUID PK, email auth), `PasswordResetToken`.

## Adding a New Django App

1. `uv run python manage.py startapp <name>`
2. Add to `INSTALLED_APPS` in [backend/app/settings.py](backend/app/settings.py)
3. Create `urls.py`, include in [backend/app/urls.py](backend/app/urls.py)

## Key Reference Files

| File                                                                                             | Purpose                                     |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| [backend/app/urls.py](backend/app/urls.py)                                                       | Full URL routing                            |
| [backend/app/settings.py](backend/app/settings.py)                                               | All config (JWT, email, Redis, AI provider) |
| [backend/organizations/permissions.py](backend/organizations/permissions.py)                     | Custom DRF permissions                      |
| [backend/job_application_analysis/workers.py](backend/job_application_analysis/workers.py)       | RQ worker pipeline                          |
| [backend/job_application_analysis/ai_service.py](backend/job_application_analysis/ai_service.py) | OpenAI/Gemini AI backend                    |
| [backend/docker-compose.yml](backend/docker-compose.yml)                                         | PostgreSQL container (port 5438)            |
| [frontend/src/proxy.ts](frontend/src/proxy.ts)                                                   | CSRF edge middleware                        |
| [frontend/src/lib/hey-api.ts](frontend/src/lib/hey-api.ts)                                       | Axios client config                         |
| [frontend/openapi-ts.config.ts](frontend/openapi-ts.config.ts)                                   | API client codegen config                   |

## API Docs

- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc
