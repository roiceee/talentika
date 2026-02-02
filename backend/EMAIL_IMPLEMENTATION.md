# Organization Invitation Email Implementation

## What's Been Implemented

✅ Email functionality for organization invitations
✅ Gmail SMTP configuration
✅ Professional HTML email template
✅ Plain text fallback for compatibility
✅ Integration with invite user endpoint

## Files Created/Modified

### New Files:

- `backend/organizations/emails.py` - Email utility functions and templates
- `backend/EMAIL_SETUP.md` - Complete guide for setting up email

### Modified Files:

- `backend/.env.example` - Added email and frontend URL configuration
- `backend/app/settings.py` - Added email backend configuration
- `backend/organizations/views.py` - Updated invite endpoint to send emails
- `backend/README.md` - Added email configuration section

## How It Works

When an organization admin invites a user:

1. **API Call** → Admin calls `/api/organizations/{org_id}/invite/`
2. **Validation** → System checks permissions and organization status
3. **Membership Created** → User is added to organization
4. **Email Sent** → Invitation email is sent to the user
5. **Response** → API returns membership data + `email_sent` flag

## Email Content

The invitation email includes:

- **Subject:** "You've been invited to join [Organization Name] on Talentika"
- **Greeting** with user's name
- **Organization details** (name, invited by)
- **Call-to-action button** linking to frontend app
- **Professional styling** with Talentika branding

## Environment Variables Required

```env
# Email Configuration (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
```

## How to Set Up

### 1. Generate Gmail App Password

1. Go to Google Account → Security → 2-Step Verification
2. Enable 2-Step Verification if not enabled
3. Go to App passwords
4. Generate password for "Mail" app
5. Copy the 16-character password

### 2. Update .env File

```bash
cp .env.example .env
# Edit .env with your email credentials
```

### 3. Test Email Sending

```bash
# Using Django shell
uv run python manage.py shell

from organizations.models import User, Organization
from organizations.emails import send_invitation_email

invited_user = User.objects.first()
organization = Organization.objects.first()
invited_by = User.objects.last()

send_invitation_email(invited_user, organization, invited_by)
```

## API Example

```bash
# 1. Login as organization admin
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# 2. Invite user to organization
curl -X POST http://localhost:8000/api/organizations/1/invite/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"user_id": 2, "role": "MEMBER"}'
```

**Response:**

```json
{
  "id": 1,
  "user": {
    "id": 2,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "organization": 1,
  "organization_name": "Acme Corp",
  "role": "MEMBER",
  "created_at": "2026-02-01T12:00:00Z",
  "email_sent": true
}
```

## Email Template Preview

```
Subject: You've been invited to join Acme Corp on Talentika

Hello John Doe,

Great news! You've been invited to join an organization on Talentika.

┌─────────────────────────────────────┐
│ Organization: Acme Corp             │
│ Invited by: Jane Admin              │
│             (admin@example.com)     │
└─────────────────────────────────────┘

Click the button below to access your organization dashboard:

        [ Go to Talentika ]

Once you log in, you'll have access to all organization features.
```

## Error Handling

The email function returns `True` if sent successfully, `False` otherwise.

The API response includes `email_sent` field to indicate email status:

- `true` - Email sent successfully
- `false` - Email failed (membership still created)

Errors are logged to console (in production, use proper logging).

## Testing

All existing tests pass with email functionality:

```bash
uv run python manage.py test organizations
# 18 tests pass
```

## Production Considerations

For production, consider:

- Using transactional email service (SendGrid, SES, etc.)
- Implementing email queue for better performance
- Adding retry logic for failed emails
- Proper error logging and monitoring
- Rate limiting on invitation endpoints

## Documentation

For complete setup instructions, see:

- [EMAIL_SETUP.md](EMAIL_SETUP.md) - Detailed email configuration guide
- [README.md](README.md) - Quick start guide
