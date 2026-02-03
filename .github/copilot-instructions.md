# Talentika - AI Coding Agent Instructions

## Project Overview

Talentika is a Django 6.0 REST API backend with PostgreSQL database, using modern Python tooling (uv package manager, Python 3.13+). The frontend folder exists but is currently empty.

**Core Domain**: Multi-tenant organization management system with email-based invitations and JWT authentication. Users can belong to multiple organizations simultaneously.

## Architecture & Structure

### Backend Organization

- **`backend/app/`**: Main Django project configuration (settings, URLs, WSGI/ASGI)
- **`backend/organizations/`**: Core app with custom User model, organizations, memberships, invitations, and JWT auth
- **`backend/health/`**: Simple health check endpoint
- Apps use **modular structure**: `models/`, `views/`, `tests/` subdirectories instead of single files (see [organizations/](backend/organizations/))

### Multi-Organization Domain Model

Critical relationships (see [organizations/models/\_\_init\_\_.py](backend/organizations/models/__init__.py)):

1. **User** (custom model) → replaces Django's default, uses email for authentication
2. **Organization** → has Status workflow (PENDING/APPROVED/REJECTED/SUSPENDED)
3. **OrganizationMembership** → many-to-many with Role (ORG_ADMIN/MEMBER)
4. **OrganizationInvitation** → token-based with 7-day expiration
5. **Address** → optional foreign key on Organization

**Key Constraints**:

- User + Organization = unique membership (no duplicate memberships)
- Only APPROVED organizations can send invitations
- Organizations auto-approve when created via API (not via Django admin)
- Invitations are single-use with email validation

### Permission System

Custom DRF permissions (see [organizations/permissions.py](backend/organizations/permissions.py)):

- `IsOrganizationAdmin` - checks `org_id` URL kwarg + membership role
- `IsOrganizationMember` - allows superusers + checks membership
- `IsOrgAdminOfOwnOrganization` - validates user is admin of specific org

Helper functions in [models/helpers.py](backend/organizations/models/helpers.py):

- `is_org_admin(user, organization)` - checks role or superuser
- `get_user_organizations(user)` - returns all orgs user belongs to

### Configuration Management

- Environment variables loaded via `python-dotenv` in [app/settings.py](backend/app/settings.py#L17)
- **Custom User Model**: `AUTH_USER_MODEL = "organizations.User"` (L54)
- **JWT Configuration**: Uses `rest_framework_simplejwt` with 1-hour access tokens, 7-day refresh (L156-169)
- **Email SMTP**: Gmail via TLS on port 587, requires app password (L146-151)
- **APPEND_SLASH = False**: URLs must match exactly without trailing slashes (L36)

### Database

- PostgreSQL 16 (Alpine) runs in Docker on port **5438** (not default 5432)
- Connection details in `docker-compose.yml` and `.env`
- Database name: `talentika_dev`, user: `talentika_user`

## Developer Workflows

### Starting Development

**Always use the dev script**: `./backend/dev.sh`
This orchestrates the entire startup:

1. Starts PostgreSQL container via docker-compose
2. Waits for `pg_isready` health check
3. Runs migrations automatically
4. Starts Django dev server on http://localhost:8000

**Do not** run `manage.py runserver` directly without ensuring database is up.

### Running Commands

All Python commands use **uv** package manager:

```bash
uv run python manage.py <command>  # NOT just python manage.py
```

Common commands:

- Migrations: `uv run python manage.py makemigrations && uv run python manage.py migrate`
- Create superuser: `uv run python manage.py createsuperuser`
- Shell: `uv run python manage.py shell`
- Tests: `uv run python manage.py test organizations.tests`

### Testing Strategy

Tests organized by domain (see [organizations/tests/README.md](backend/organizations/tests/README.md)):

- `test_authentication.py` - User registration & JWT login (5 tests)
- `test_organizations.py` - Org creation, membership, permissions (18 tests)
- `test_invitations.py` - Email invitations, validation, acceptance (37 tests)

Run specific test modules: `uv run python manage.py test organizations.tests.test_invitations`

### Database Management

- Start database only: `docker compose up -d` (from backend/)
- Stop database: `docker compose down`
- Reset database: `docker compose down -v` (deletes all data)

## API Documentation

API docs are auto-generated using **drf-yasg**:

- Swagger UI: http://localhost:8000/swagger (includes "Authorize" button for Bearer tokens)
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Documenting Endpoints

Use `@swagger_auto_schema` decorator on API views (see [organizations/views/invitations.py](backend/organizations/views/invitations.py#L27-L59)):

```python
@swagger_auto_schema(
    method='post',
    operation_description="...",
    manual_parameters=[openapi.Parameter('org_id', openapi.IN_PATH, ...)],
    request_body=InvitationCreateSerializer,
    responses={201: OrganizationInvitationSerializer, ...},
    tags=['Invitations']
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrgAdminOfOwnOrganization])
def create_invitation(request, org_id):
    ...
```

## Project Conventions

### Authentication Pattern

Email-based JWT auth (see [organizations/authentication.py](backend/organizations/authentication.py)):

- Custom serializer: `EmailTokenObtainPairSerializer` uses email instead of username
- Login endpoint: `POST /api/auth/login/` with `{"email": "...", "password": "..."}`
- Returns `access` (1h) and `refresh` (7d) tokens
- Use in headers: `Authorization: Bearer <access_token>`

### Invitation Flow

Complete workflow documented in [INVITATION_FLOW.md](backend/INVITATION_FLOW.md):

1. Admin creates invitation: `POST /api/organizations/{org_id}/invitations/`
2. Email sent with secure token (7-day expiration)
3. **New users**: Register with token: `POST /api/register/` (auto-joins org)
4. **Existing users**: Accept invitation: `POST /api/invitations/accept/`

Critical validations:

- Email must match invitation
- Token expires after 7 days
- Single-use tokens (check `accepted_at` field)
- Cannot join same org twice

### When Adding New Django Apps

1. Create app: `uv run python manage.py startapp <app_name>`
2. Add to `INSTALLED_APPS` in [app/settings.py](backend/app/settings.py#L41)
3. Create `urls.py` in app directory
4. Include in main [app/urls.py](backend/app/urls.py): `path("<prefix>/", include("<app_name>.urls"))`

### API Views Pattern

- Use DRF function-based views with `@api_view()` decorator
- Always add Swagger documentation decorators with `tags=["..."]` for grouping
- Return `Response()` objects from `rest_framework.response`
- Use custom permission classes from [permissions.py](backend/organizations/permissions.py)

### URL Routing Convention

**Important**: `APPEND_SLASH = False` means URLs must not have trailing slashes:

- ✅ `/api/organizations/`
- ❌ `/api/organizations` (404)

URL includes pattern (see [app/urls.py](backend/app/urls.py#L35)):

```python
path("api/", include("organizations.urls"))  # Organizations handles auth + org endpoints
```

## Tech Stack

- **Framework**: Django 6.0.1 + Django REST Framework 3.16.1
- **Database**: PostgreSQL 16 (via psycopg2-binary)
- **Authentication**: djangorestframework-simplejwt (email-based)
- **API Docs**: drf-yasg (Swagger/OpenAPI)
- **Email**: SMTP via Gmail (requires app password)
- **Package Manager**: uv (not pip/poetry)
- **Python**: 3.13+ (see `.python-version`)
- **Container**: Docker Compose for database only

## Key Files

- [backend/dev.sh](backend/dev.sh): Development startup script
- [backend/INVITATION_FLOW.md](backend/INVITATION_FLOW.md): Complete invitation system documentation
- [backend/app/settings.py](backend/app/settings.py): All Django configuration including JWT & email
- [backend/app/urls.py](backend/app/urls.py): Main URL routing + Swagger setup
- [backend/organizations/models/\_\_init\_\_.py](backend/organizations/models/__init__.py): All models + helper functions
- [backend/organizations/permissions.py](backend/organizations/permissions.py): Custom DRF permissions
- [backend/docker-compose.yml](backend/docker-compose.yml): PostgreSQL container config
