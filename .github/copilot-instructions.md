# Talentika - AI Coding Agent Instructions

## Project Overview

Talentika is a Django 6.0 REST API backend with PostgreSQL database, using modern Python tooling (uv package manager, Python 3.13+). The frontend folder exists but is currently empty.

## Architecture & Structure

### Backend Organization

- **`backend/app/`**: Main Django project configuration (settings, URLs, WSGI/ASGI)
- **`backend/health/`**: Example Django app with health check endpoint
- Apps follow Django's standard structure: `views.py`, `urls.py`, `models.py`, `admin.py`
- URL routing: App URLs included in main `app/urls.py` via `include()`

### Configuration Management

- Environment variables loaded via `python-dotenv` in [app/settings.py](backend/app/settings.py#L17)
- Settings use `os.getenv()` with sensible defaults for development
- Database config, DEBUG mode, SECRET_KEY, and ALLOWED_HOSTS all environment-driven
- See [.env.example](backend/.env.example) for all available variables

### Database

- PostgreSQL 16 (Alpine) runs in Docker on port **5438** (not default 5432)
- Connection details in `docker-compose.yml` and `.env`
- Database name: `talentika_dev`, user: `talentika_user`

## Developer Workflows

### Starting Development

**Always use the dev script**: `./backend/dev.sh`
This orchestrates the entire startup:

1. Starts PostgreSQL container via docker-compose
2. Waits for database health check
3. Runs migrations automatically
4. Starts Django dev server on http://localhost:8000

**Do not** run `manage.py runserver` directly without ensuring database is up.

### Running Commands

All Python commands use **uv** package manager:

```bash
uv run python manage.py <command>  # NOT just python manage.py
```

Common commands:

- Migrations: `uv run python manage.py migrate`
- Create superuser: `uv run python manage.py createsuperuser`
- Shell: `uv run python manage.py shell`

### Database Management

- Start database only: `docker compose up -d` (from backend/)
- Stop database: `docker compose down`
- Reset database: `docker compose down -v` (deletes all data)

## API Documentation

API docs are auto-generated using **drf-yasg**:

- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/swagger.json

### Documenting Endpoints

Use `@swagger_auto_schema` decorator on API views (see [health/views.py](backend/health/views.py#L8-L15)):

```python
@swagger_auto_schema(method='get',
                     operation_description="...",
                     responses={200: openapi.Response(...)})
@api_view(["GET"])
def my_view(request):
    ...
```

## Project Conventions

### When Adding New Django Apps

1. Create app: `uv run python manage.py startapp <app_name>`
2. Add to `INSTALLED_APPS` in [app/settings.py](backend/app/settings.py#L41)
3. Create `urls.py` in app directory
4. Include in main [app/urls.py](backend/app/urls.py): `path("<prefix>/", include("<app_name>.urls"))`

### API Views Pattern

- Use DRF function-based views with `@api_view()` decorator
- Always add Swagger documentation decorators
- Return `Response()` objects from `rest_framework.response`

### Database Port Note

PostgreSQL runs on **port 5438** externally (mapped from internal 5432) to avoid conflicts. Update `.env` if changing this.

## Tech Stack

- **Framework**: Django 6.0.1 + Django REST Framework 3.16.1
- **Database**: PostgreSQL 16 (via psycopg2-binary)
- **API Docs**: drf-yasg (Swagger/OpenAPI)
- **Package Manager**: uv (not pip/poetry)
- **Python**: 3.13+ (see `.python-version`)
- **Container**: Docker Compose for database only

## Key Files

- [backend/dev.sh](backend/dev.sh): Development startup script
- [backend/app/settings.py](backend/app/settings.py): All Django configuration
- [backend/app/urls.py](backend/app/urls.py): Main URL routing + Swagger setup
- [backend/docker-compose.yml](backend/docker-compose.yml): PostgreSQL container config
- [backend/.env.example](backend/.env.example): Required environment variables
