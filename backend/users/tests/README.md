# Users App Tests

This directory contains test files for the users app functionality.

## Test Structure

- `test_authentication.py` - Tests for user registration and JWT authentication
- `test_profile.py` - Tests for user profile management (get/update)
- `test_password_reset.py` - Tests for password reset workflow

## Running Tests

Run all users app tests:

```bash
uv run python manage.py test users.tests
```

Run specific test module:

```bash
uv run python manage.py test users.tests.test_authentication
uv run python manage.py test users.tests.test_profile
uv run python manage.py test users.tests.test_password_reset
```

## Test Coverage Areas

### Authentication Tests

- User registration without invitation
- User registration with valid invitation token
- Login with email and password
- Token refresh functionality
- Invalid credentials handling

### Profile Tests

- Get user profile (authenticated)
- Update profile with PUT (full update)
- Update profile with PATCH (partial update)
- Email update prevention
- Username uniqueness validation
- Unauthorized access prevention

### Password Reset Tests

- Request password reset with valid email
- Request password reset with non-existent email (security)
- Confirm password reset with valid token
- Invalid token handling
- Expired token handling
- Password mismatch validation
