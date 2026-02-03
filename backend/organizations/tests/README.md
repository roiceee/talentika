# Test Organization Structure

The test suite has been reorganized into a modular structure with separate test files for different concerns.

## Test Directory Structure

```
backend/organizations/tests/
├── __init__.py
├── test_authentication.py       # User registration and JWT authentication (5 tests)
├── test_organizations.py        # Organization models and permissions (18 tests)
└── test_invitations.py          # Invitation system (37 tests)
```

## Test Files Overview

### test_authentication.py (5 tests)

Tests for user registration and JWT authentication:

- **UserRegistrationTests** - User registration workflow
  - Successful registration
  - Password mismatch validation
  - Duplicate email prevention
- **AuthenticationTests** - JWT authentication
  - Login with email
  - Invalid credentials handling

### test_organizations.py (18 tests)

Tests for organization management and permissions:

- **OrganizationModelTests** - Organization model methods
  - Default PENDING status
  - Approval/rejection workflow
  - Invitation permissions for approved orgs
- **OrganizationCreationTests** - Organization creation via API
  - Auto-approval on creation
  - Creator becomes ORG_ADMIN
  - Authentication requirements
- **OrganizationMembershipTests** - Membership and permissions
  - Admin permission checks
  - Member listing permissions
  - Helper function validation
- **SuperAdminTests** - Super admin access control
  - Pending organization management
  - Approval/rejection permissions
- **OrganizationPermissionTests** - Permission helper functions
  - User organization retrieval

### test_invitations.py (37 tests)

Comprehensive tests for the invitation system:

#### OrganizationInvitationModelTests (12 tests)

Model-level invitation functionality:

- Token auto-generation and uniqueness
- Expiration auto-setting and configuration
- Validation state checks (valid, expired, accepted)
- Accept method functionality
- String representation
- Role assignment (MEMBER, ORG_ADMIN)

#### InvitationCreationAPITests (11 tests)

API endpoint for creating invitations:

- Successful invitation creation by admin
- Admin role invitations
- Permission requirements (admin, authenticated, organization membership)
- Email validation
- Duplicate prevention for pending invitations
- Re-invitation after acceptance
- Invited-by tracking

#### InvitationValidationAPITests (6 tests)

Token validation endpoint:

- Valid token validation
- Invalid token handling
- Expired token detection
- Already-accepted token detection
- No authentication required
- Missing token validation

#### InvitationAcceptanceAPITests (9 tests)

Invitation acceptance workflow:

- Successful acceptance with correct email
- Role assignment on acceptance
- Authentication requirements
- Email mismatch prevention
- Expired invitation rejection
- Duplicate acceptance prevention
- Invalid token handling
- Already-member prevention

#### InvitationEmailTests (1 test)

Email functionality:

- Email sending on invitation creation

## Running Tests

```bash
# Run all organization tests (55 tests)
uv run python manage.py test organizations

# Run specific test modules
uv run python manage.py test organizations.tests.test_authentication
uv run python manage.py test organizations.tests.test_organizations
uv run python manage.py test organizations.tests.test_invitations

# Run specific test class
uv run python manage.py test organizations.tests.test_invitations.InvitationCreationAPITests

# Run specific test method
uv run python manage.py test organizations.tests.test_invitations.InvitationCreationAPITests.test_create_invitation_as_admin_success
```

## Test Coverage Summary

- ✅ 5 authentication tests
- ✅ 18 organization management tests
- ✅ 37 invitation system tests
- **Total: 55 tests, all passing**

## Key Testing Patterns

### Authentication

All API tests use `self.client.force_authenticate(user=<user>)` to simulate authenticated requests.

### Test Data Setup

Each test class has a `setUp()` method that creates necessary test fixtures (users, organizations, memberships).

### Assertions

Tests use Django's assertion methods:

- `assertEqual()` - value equality
- `assertTrue()/assertFalse()` - boolean checks
- `assertIn()` - substring/item checks
- `assertIsNotNone()/assertIsNone()` - null checks

### API Response Validation

Tests verify:

- HTTP status codes
- Response data structure
- Database state changes
- Permission enforcement
- Error message content
