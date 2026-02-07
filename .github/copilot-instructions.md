# Talentika - AI Coding Agent Instructions

## Project Overview

Talentika is a Django 6.0 REST API backend with PostgreSQL database, using modern Python tooling (uv package manager, Python 3.13+). The frontend folder exists but is currently empty.

**Core Domain**: Multi-tenant organization management system with email-based invitations and JWT authentication. Users can belong to multiple organizations simultaneously.

## Architecture & Structure

### Backend Organization

- **`backend/app/`**: Main Django project configuration (settings, URLs, WSGI/ASGI)
- **`backend/users/`**: User authentication, profile management, and password reset functionality
- **`backend/organizations/`**: Organizations, memberships, and invitation system
- **`backend/health/`**: Simple health check endpoint
- Apps use **modular structure**: `models/`, `views/`, `serializers/`, `tests/` subdirectories instead of single files

### Domain Model

Critical relationships:

**Users App** (see [users/models.py](backend/users/models.py)):

1. **User** (custom model) → replaces Django's default, uses email for authentication (`AbstractUser` with UUID primary key)
2. **PasswordResetToken** → secure 24-hour tokens for password resets

**Organizations App** (see [organizations/models/\_\_init\_\_.py](backend/organizations/models/__init__.py)):

1. **Organization** → has Status workflow (PENDING/APPROVED/REJECTED/SUSPENDED)
2. **OrganizationMembership** → many-to-many with Role (ORG_ADMIN/MEMBER), links User to Organization
3. **OrganizationInvitation** → token-based with 7-day expiration
4. **Address** → optional foreign key on Organization

**Key Constraints**:

- User + Organization = unique membership (no duplicate memberships)
- Only APPROVED organizations can send invitations
- Organizations auto-approve when created via API (not via Django admin)
- Invitations are single-use with email validation
- Password reset tokens expire in 24 hours and are single-use

### API Routing Structure

URL organization (see [app/urls.py](backend/app/urls.py)):

```python
path("api/users/", include("users.urls"))      # User auth, profile, password reset
path("api/", include("organizations.urls"))     # Organizations, memberships, invitations
```

**Users App Endpoints** (`/api/users/`):

- `POST /auth/register/` - User registration (optional invitation token)
- `POST /auth/login/` - Email-based login (returns JWT tokens)
- `POST /auth/token/refresh/` - Refresh JWT token
- `GET /profile/` - Get current user profile
- `PUT|PATCH /profile/update/` - Update profile (username, first_name, last_name)
- `POST /password-reset/` - Request password reset email
- `POST /password-reset/confirm/` - Confirm reset with token

**Organizations App Endpoints** (`/api/`):

- Organizations: `/organizations/`, `/organizations/create/`, `/organizations/<uuid:org_id>/`
- Members: `/organizations/<uuid:org_id>/members/`, leave/remove operations
- Invitations: `/organizations/<uuid:org_id>/invitations/`, accept/validate operations

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
- **Custom User Model**: `AUTH_USER_MODEL = "users.User"` (L56) - moved from organizations to users app
- **JWT Configuration**: Uses `rest_framework_simplejwt` with 1-hour access tokens, 7-day refresh (L159-172)
- **Email SMTP**: Gmail via TLS on port 587, requires app password (L149-154)
- **APPEND_SLASH = False**: URLs must match exactly without trailing slashes (L38)
- **FRONTEND_URL**: Required for password reset and invitation email links (default: `http://localhost:3000`)

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

Tests organized by domain:

**Organizations App** (see [organizations/tests/README.md](backend/organizations/tests/README.md)):

- `test_authentication.py` - User registration & JWT login (5 tests)
- `test_organizations.py` - Org creation, membership, permissions (18 tests)
- `test_invitations.py` - Email invitations, validation, acceptance (37 tests)

**Users App** (see [users/tests/README.md](backend/users/tests/README.md)):

- `test_authentication.py` - User registration with/without invitation tokens
- `test_profile.py` - Profile retrieval and updates (full/partial)
- `test_password_reset.py` - Password reset request and token confirmation

Run specific test modules:

```bash
uv run python manage.py test organizations.tests.test_invitations
uv run python manage.py test users.tests.test_password_reset
```

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

Email-based JWT auth split across two apps:

**Users App** (see [users/authentication.py](backend/users/authentication.py)):

- Custom serializer: `EmailTokenObtainPairSerializer` uses email instead of username
- Login endpoint: `POST /api/users/auth/login/` with `{"email": "...", "password": "..."}`
- Returns `access` (1h) and `refresh` (7d) tokens
- Use in headers: `Authorization: Bearer <access_token>`

**Organizations App** (see [organizations/authentication.py](backend/organizations/authentication.py)):

- Legacy authentication module (maintained for backward compatibility)
- New authentication endpoints use users app

### Password Reset Flow

Secure token-based password reset (see [users/views/password_reset.py](backend/users/views/password_reset.py)):

1. User requests reset: `POST /api/users/password-reset/` with email
2. Email sent with secure token (24-hour expiration)
3. Frontend redirects to: `{FRONTEND_URL}/password-reset/{token}/`
4. User confirms: `POST /api/users/password-reset/confirm/` with token and new password

Critical validations:

- Token is single-use (checked via `used_at` field)
- Tokens expire in 24 hours
- Response doesn't reveal if email exists (security best practice)

### Invitation Flow

Complete workflow documented in [INVITATION_FLOW.md](backend/INVITATION_FLOW.md):

1. Admin creates invitation: `POST /api/organizations/{org_id}/invitations/`
2. Email sent with secure token (7-day expiration)
3. **New users**: Register with token: `POST /api/users/auth/register/` (auto-joins org)
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
path("api/users/", include("users.urls"))       # User auth & profile management
path("api/", include("organizations.urls"))     # Organizations, memberships, invitations
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
