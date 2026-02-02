# Talentika Development Setup

## Prerequisites

- Docker and Docker Compose
- Python 3.13+
- uv package manager

## Quick Start

1. **Start the development environment:**

   ```bash
   ./dev.sh
   ```

   This script will:
   - Start PostgreSQL in a Docker container
   - Wait for the database to be ready
   - Run Django migrations
   - Start the Django development server

2. **Access the application:**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Swagger API Docs: http://localhost:8000/swagger
   - ReDoc API Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Authentication

Talentika uses JWT (JSON Web Token) authentication with email-based login.

**Quick Test:**

```bash
# Register a user
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# Login to get tokens
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'

# Use the access token for authenticated requests
curl -X GET http://localhost:8000/api/organizations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

For complete authentication documentation, see [AUTHENTICATION.md](AUTHENTICATION.md).

**Testing with Swagger UI:**

1. Go to http://localhost:8000/swagger/
2. Click the "Authorize" button (lock icon)
3. Enter: `Bearer YOUR_ACCESS_TOKEN`
4. All API calls will now be authenticated

## Email Configuration

Talentika sends invitation emails when users are added to organizations. To enable email functionality:

1. **Set up Gmail SMTP** (see [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed instructions)
2. **Update your `.env` file:**

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:3000
```

For complete email setup instructions, including how to generate Gmail app passwords, see [EMAIL_SETUP.md](EMAIL_SETUP.md).

## Manual Setup

If you prefer to run services separately:

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Install Dependencies

```bash
cd backend
uv sync
```

### 3. Configure Environment

Copy the example environment file:

```bash
cp backend/.env.example backend/.env
```

Edit `.env` with your configuration if needed.

### 4. Run Migrations

```bash
cd backend
uv run python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
uv run python manage.py createsuperuser
```

### 6. Start Development Server

```bash
uv run python manage.py runserver
```

## Database Configuration

The PostgreSQL database runs in Docker with the following default credentials:

- **Database:** talentika_dev
- **User:** talentika_user
- **Password:** talentika_password
- **Host:** localhost
- **Port:** 5432

You can modify these in `docker-compose.yml` and `backend/.env`.

## Stopping Services

### Stop Django server

Press `Ctrl+C` in the terminal running the dev server.

### Stop PostgreSQL

```bash
docker compose down
```

### Stop and remove volumes (WARNING: This will delete your database)

```bash
docker compose down -v
```

## Database Management

### Access PostgreSQL CLI

```bash
docker compose exec postgres psql -U talentika_user -d talentika_dev
```

### View Database Logs

```bash
docker compose logs postgres
```

### Backup Database

```bash
docker compose exec postgres pg_dump -U talentika_user talentika_dev > backup.sql
```

### Restore Database

```bash
docker compose exec -T postgres psql -U talentika_user -d talentika_dev < backup.sql
```

## Troubleshooting

### Port 5432 already in use

If you have another PostgreSQL instance running, either stop it or change the port in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432" # Use port 5433 instead
```

Then update `DB_PORT` in `backend/.env` to `5433`.

### Connection refused

Make sure the PostgreSQL container is running and healthy:

```bash
docker compose ps
```

### Migration errors

Reset the database (WARNING: This will delete all data):

```bash
docker compose down -v
docker compose up -d
cd backend
uv run python manage.py migrate
```
