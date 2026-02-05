# App Module (Core Configuration) - Business Logic Documentation

## Overview

The `app` module is the central configuration hub for Talentika. It orchestrates how all modules interact and defines operational parameters. This module does not contain business logic but enables all business logic to function.

## Purpose & Responsibilities

### 1. Application Configuration
- Database connection settings
- Authentication and authorization setup
- Email service configuration
- API framework settings
- Security settings

### 2. URL Routing (API Gateway)
Routes all HTTP requests to appropriate modules:
- `/admin/` → Django admin interface
- `/health` → Health check endpoint
- `/api/` → Organizations module (all business logic)
- `/swagger/`, `/redoc/` → API documentation

### 3. Integration Hub
Connects system components:
- Django REST Framework (API layer)
- JWT authentication system
- Swagger/OpenAPI documentation
- PostgreSQL database
- Email service (SMTP)

## Key Configuration Areas

### 1. Custom User Model

**Configuration**: Uses `organizations.User` as authentication model

**Business Impact**:
- Users authenticate with email address (no username)
- Simplifies user experience
- All system references point to custom User model

### 2. JWT Authentication

**Token Configuration**:
- **Access Token**: 1 hour lifetime
- **Refresh Token**: 7 days lifetime
- **Algorithm**: HS256 (symmetric signing)

**Business Impact**:
- Access tokens expire quickly for security
- Refresh tokens balance security with user experience
- Users don't need to login constantly

### 3. Email Service

**Configuration**: Gmail SMTP on port 587 with TLS

**Business Usage**:
- Send organization invitations
- Future: Password reset emails
- Future: Notification emails

### 4. Database Connection

**Configuration**: PostgreSQL 16 on port 5438

**Business Impact**:
- Robust data integrity
- Support for complex queries
- Logical separation of organization data

### 5. API Framework (Django REST Framework)

**Default Settings**:
- **Authentication**: JWT required by default
- **Permission**: All endpoints require authentication by default
- **Format**: JSON only

**Business Impact**:
- Secure by default (must explicitly make endpoints public)
- Consistent API format
- Reduces accidental data exposure

### 6. URL Slash Handling

**Configuration**: `APPEND_SLASH = False`

**Business Impact**:
- URLs must match exactly: `/api/organizations/` works, `/api/organizations` returns 404
- Frontend must use consistent URL format
- Prevents confusion with automatic redirects

## URL Routing Structure

**Main Routes**:
```
/admin/              → Django admin (staff only)
/health              → Public health check
/api/                → All business endpoints (organizations module)
/swagger/            → Interactive API docs
/redoc/              → Clean API documentation
```

**Delegation Pattern**:
- Main app routes to modules
- Each module manages its own URLs
- Clear separation of concerns

## API Documentation System

**Access Points**:
- **Swagger UI**: http://localhost:8000/swagger/ - Interactive testing
- **ReDoc**: http://localhost:8000/redoc/ - Clean documentation
- **OpenAPI JSON**: http://localhost:8000/swagger.json - Machine-readable

**Business Value**:
- Self-documenting API
- Frontend developers can test endpoints
- Can generate client SDKs automatically

## Environment Variables

**Required Configuration**:
```
# Core
SECRET_KEY=<secure-random-string>
DEBUG=False (production)
ALLOWED_HOSTS=example.com

# Database
POSTGRES_DB=talentika_prod
POSTGRES_USER=talentika_user
POSTGRES_PASSWORD=<secure>
POSTGRES_HOST=db.example.com
POSTGRES_PORT=5432

# Email
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=<gmail-app-password>
DEFAULT_FROM_EMAIL=Talentika <noreply@example.com>
```

## Security Configuration

**Key Security Settings**:
- **SECRET_KEY**: Used for cryptographic signing (tokens, sessions)
- **DEBUG**: Must be False in production (hides error details)
- **ALLOWED_HOSTS**: Prevents host header injection attacks

**JWT Security**:
- Access tokens expire quickly (1 hour)
- Refresh tokens have reasonable lifetime (7 days)
- Tokens signed with SECRET_KEY

## Integration Points

### Backend ↔ Database
- **Protocol**: PostgreSQL wire protocol
- **Access**: Django ORM abstracts SQL
- **Migrations**: Version-controlled schema changes

### Backend ↔ Email Service
- **Protocol**: SMTP over TLS
- **Provider**: Gmail
- **Usage**: Invitation emails

### Backend ↔ Frontend
- **Protocol**: HTTPS REST API
- **Format**: JSON
- **Authentication**: JWT Bearer tokens

## Application Lifecycle

### Startup Sequence
1. Load configuration from settings
2. Connect to PostgreSQL database
3. Initialize installed apps (health, organizations)
4. Configure middleware stack
5. Load URL routing
6. Application ready to serve requests

### Deployment Process
1. Set environment variables
2. Run database migrations
3. Start web server (Gunicorn in production)
4. Configure reverse proxy (NGINX)
5. Health check validates deployment

## Module Coordination

The app module enables these business workflows:

**User Registration Flow**:
```
Frontend Request → App Routes → Organizations Module → Database
                                                     → Email Service
```

**Health Check Flow**:
```
Load Balancer → App Routes → Health Module → Response
```

**API Documentation Access**:
```
Developer → App Routes → Swagger UI → Interactive Docs
```

## Relationship to Business Modules

### Health Module
- App provides URL routing to health endpoint
- No authentication configured for health check
- Public access enabled

### Organizations Module
- App routes all `/api/` requests to organizations
- JWT authentication configured
- Email service available for invitations
- Database connection configured

## Conclusion

The app module is the **orchestration layer** that:
- Routes requests to appropriate handlers
- Configures authentication and security
- Connects external services (database, email)
- Provides API documentation
- Defines application lifecycle

While it contains no business logic, it is **essential** for:
- System reliability
- Security enforcement
- Module integration
- API design consistency
