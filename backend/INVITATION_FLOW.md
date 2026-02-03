# Email-Based Invitation System

## Overview

Talentika uses an **email-based invitation system** that allows organizations to invite both existing and non-existing users. **Users can belong to multiple organizations** simultaneously. Invitations are sent via email with a secure token, and users can join organizations either by accepting an invitation if they already have an account, or by registering with the invitation token if they don't.

## Key Features

### Multiple Organization Support

- **Users can join multiple organizations** - no limit on the number of organizations a user can belong to
- Each membership is independent with its own role (member or admin)
- Users cannot join the same organization twice (unique constraint)

## How It Works

### 1. Creating an Invitation

**Endpoint:** `POST /api/invitations/`

Organization admins can create invitations by providing an email address and role.

```json
{
  "email": "newuser@example.com",
  "role": "member"
}
```

**Response:**

```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "role": "member",
  "invitation_token": "secure-token",
  "expires_at": "2025-06-01T00:00:00Z",
  "is_accepted": false,
  "created_at": "2025-05-24T00:00:00Z"
}
```

An email is sent to the recipient with:

- Organization details
- Invitation expiration date (7 days)
- The secure invitation token
- Instructions to either register (if new) or accept (if existing user)

### 2. User Registration with Invitation (New Users)

**Endpoint:** `POST /api/register/`

New users can register and automatically join an organization by including the invitation token:

```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "invitation_token": "secure-token"
}
```

**What happens:**

1. System validates the invitation token
2. Checks if token is expired (7 days from creation)
3. Verifies email matches the invitation
4. Creates the user account
5. **Automatically creates organization membership** with the specified role
6. Marks invitation as accepted

**Validation errors:**

- `"Invalid or expired invitation token"` - Token not found or expired
- `"This invitation has already been accepted"` - Token already used
- `"Email does not match the invitation"` - Email mismatch

### 3. Accepting an Invitation (Existing Users)

**Endpoint:** `POST /api/invitations/accept/`

Existing users who receive an invitation must accept it explicitly:

```json
{
  "invitation_token": "secure-token"
}
```

**What happens:**

1. System validates the token and checks expiration
2. Creates organization membership
3. Marks invitation as accepted

**Note:** Users can only belong to one organization, so they cannot accept an invitation if they're already a member of another organization.

### 4. Validating an Invitation

**Endpoint:** `POST /api/invitations/validate/`

Check if an invitation token is valid before attempting to use it:

```json
{
  "invitation_token": "secure-token"
}
```

**Response:**

```json
{
  "valid": true,
  "email": "newuser@example.com",
  "organization": {
    "id": "uuid",
    "name": "Example Org"
  },
  "role": "member",
  "expires_at": "2025-06-01T00:00:00Z"
}
```

## Key Features

### Security

- **Secure tokens:** Generated using `secrets.token_urlsafe(32)` (256-bit entropy)
- **Expiration:** Invitations expire after 7 days
- **One-time use:** Tokens cannot be reused after acceptance
- **Email validation:** System ensures email matches invitation

### Flexibility

- **Invite non-users:** Organizations can invite people who don't have accounts yet
- **Automatic membership:** Users joining via invitation automatically get the correct role
- **Email-only:** No need for user IDs - invitations work purely via email

### Organization Rules

- Only **approved organizations** can send invitations
- Only **organization admins** can create invitations
- Users can only belong to **one organization**
- Cannot invite email addresses that are already members

## API Endpoints Summary

| Endpoint                     | Method | Auth Required       | Description                                      |
| ---------------------------- | ------ | ------------------- | ------------------------------------------------ |
| `/api/invitations/`          | POST   | Yes (Org Admin)     | Create invitation                                |
| `/api/invitations/validate/` | POST   | No                  | Validate invitation token                        |
| `/api/invitations/accept/`   | POST   | Yes (Authenticated) | Accept invitation (existing users)               |
| `/api/register/`             | POST   | No                  | Register user (optionally with invitation_token) |

## Example Flows

### Flow 1: Inviting a New User

1. Admin creates invitation for `newperson@example.com`
2. System sends email with token `abc123xyz`
3. Recipient goes to registration page, enters:
   - Email: `newperson@example.com`
   - Username, password, etc.
   - Invitation token: `abc123xyz`
4. Account created + automatically becomes member with role specified in invitation

### Flow 2: Inviting an Existing User

1. Admin creates invitation for `existing@example.com`
2. System sends email with token `def456uvw`
3. User logs in to their existing account
4. User calls `/api/invitations/accept/` with token `def456uvw`
5. Membership created with specified role

## Error Handling

Common error scenarios:

- **Expired invitation:** Returns 400 with message about expiration
- **Already accepted:** Returns 400 indicating token was already used
- **Email mismatch:** Returns 400 if registration email doesn't match invitation
- **Already a member:** Returns 400 if user already belongs to an organization
- **Invalid token:** Returns 404 or 400 for non-existent tokens
- **Unapproved organization:** Returns 403 when org is not approved to send invitations

## Database Schema

### OrganizationInvitation Model

```python
class OrganizationInvitation:
    id: UUID
    organization: ForeignKey(Organization)
    email: EmailField (indexed)
    role: CharField (choices: member/admin)
    invitation_token: CharField (unique, indexed)
    is_accepted: BooleanField (default=False)
    accepted_by: ForeignKey(User, null=True)
    accepted_at: DateTimeField(null=True)
    expires_at: DateTimeField
    created_at: DateTimeField (auto_now_add)
    created_by: ForeignKey(User)
```

### Key Indexes

- `email` - For looking up invitations by recipient
- `invitation_token` - For fast token validation
- `is_accepted` + `expires_at` - For filtering active invitations

## Testing

Comprehensive test coverage in `organizations/tests/test_invitations.py`:

- 37 test cases covering all invitation scenarios
- Token validation, expiration, acceptance
- Registration with invitation tokens
- Error handling and edge cases

Run tests:

```bash
uv run python manage.py test organizations.tests.test_invitations
```
