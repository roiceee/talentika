# Users App - Quick Summary

## What Was Created

A new Django app `users` that handles:

1. **Authentication** (moved from organizations app)
2. **User Profile Management** (new)
3. **Password Reset** (new)

## New API Endpoints

### Authentication (moved from `/api/` to `/api/users/`)

- `POST /api/users/auth/register/` - User registration
- `POST /api/users/auth/login/` - Login with email/password
- `POST /api/users/auth/token/refresh/` - Refresh JWT token

### User Profile (NEW)

- `GET /api/users/profile/` - Get current user profile
- `PUT/PATCH /api/users/profile/update/` - Update profile (username, first_name, last_name)

### Password Reset (NEW)

- `POST /api/users/password-reset/` - Request password reset email
- `POST /api/users/password-reset/confirm/` - Confirm reset with token from email

## Key Features

### Profile Management

✅ Users can view their profile  
✅ Users can update username, first name, last name  
❌ Email cannot be changed (read-only for security)  
✅ Supports both full (PUT) and partial (PATCH) updates

### Password Reset

✅ Sends email with secure reset link  
✅ Token expires in 24 hours  
✅ Single-use tokens  
✅ Secure - doesn't reveal if email exists  
📧 Email link format: `{FRONTEND_URL}/password-reset/{uid}/{token}/`

## Quick Start

1. **View Swagger docs:** http://localhost:8000/swagger
2. **Test registration:**

   ```bash
   curl -X POST http://localhost:8000/api/users/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","username":"test","first_name":"Test","last_name":"User","password":"pass123","password_confirm":"pass123"}'
   ```

3. **Test login:**
   ```bash
   curl -X POST http://localhost:8000/api/users/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"pass123"}'
   ```

## Files Created

```
users/
├── authentication.py                  # JWT serializers
├── urls.py                            # URL routing
├── USERS_BUSINESS_LOGIC.md           # Detailed documentation
├── API_MIGRATION_GUIDE.md            # Migration guide
├── serializers/
│   ├── user_serializer.py            # User & profile serializers
│   └── password_reset_serializer.py  # Password reset serializers
├── views/
│   ├── authentication.py             # Registration view
│   ├── profile.py                    # Profile views
│   └── password_reset.py             # Password reset views
└── tests/
    ├── README.md
    ├── test_authentication.py
    ├── test_profile.py
    └── test_password_reset.py
```

## Environment Variables Required

```bash
# Password reset email configuration
FRONTEND_URL=http://localhost:3000
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## Breaking Changes

⚠️ **Authentication endpoints moved:**

- Old: `/api/auth/login/` → New: `/api/users/auth/login/`
- Old: `/api/auth/refresh/` → New: `/api/users/auth/token/refresh/`
- Old: `/api/register/` → New: `/api/users/auth/register/`

## Documentation

- **Business Logic:** [USERS_BUSINESS_LOGIC.md](USERS_BUSINESS_LOGIC.md)
- **Migration Guide:** [API_MIGRATION_GUIDE.md](API_MIGRATION_GUIDE.md)
- **Tests README:** [tests/README.md](tests/README.md)
- **Swagger UI:** http://localhost:8000/swagger (when server is running)
