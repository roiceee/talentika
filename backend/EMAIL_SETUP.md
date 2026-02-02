# Email Configuration Guide

This guide explains how to set up email functionality for Talentika, specifically for sending organization invitation emails.

## Gmail SMTP Setup

### 1. Generate App Password

Since Gmail requires app-specific passwords for SMTP access, follow these steps:

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** > **2-Step Verification** (enable it if not already enabled)
3. Scroll down to **App passwords**
4. Click on **App passwords**
5. Select **Mail** as the app and **Other** as the device
6. Enter "Talentika Backend" as the device name
7. Click **Generate**
8. Copy the 16-character password (you'll use this as `EMAIL_HOST_PASSWORD`)

### 2. Update Environment Variables

Copy `.env.example` to `.env` if you haven't already:

```bash
cp .env.example .env
```

Update the following email variables in your `.env` file:

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

**Important:**

- Use the 16-character app password, NOT your regular Gmail password
- Replace `your-email@gmail.com` with your actual Gmail address
- Update `FRONTEND_URL` to your actual frontend URL (default is http://localhost:3000)

## Email Templates

The invitation email includes:

- A personalized greeting
- Organization name and details
- Name and email of the person who sent the invitation
- A call-to-action button linking to the frontend application
- Both HTML and plain text versions for compatibility

### Email Preview

**Subject:** You've been invited to join [Organization Name] on Talentika

**Content:**

- Organization name
- Invited by (name and email)
- Button linking to frontend application
- Professional styling with Talentika branding

## Testing Email Functionality

### 1. Using Django Shell

```python
uv run python manage.py shell

from organizations.models import User, Organization
from organizations.emails import send_invitation_email

# Get test users and organization
invited_user = User.objects.get(email="test@example.com")
organization = Organization.objects.first()
invited_by = User.objects.get(email="admin@example.com")

# Send test email
send_invitation_email(invited_user, organization, invited_by)
```

### 2. Using the API

1. Create two users (inviter and invitee)
2. Create and approve an organization
3. Make the inviter an organization admin
4. Call the invite endpoint:

```bash
# Login as admin
curl -X POST http://localhost:8000/api/organizations/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Invite user (use the access token from login)
curl -X POST http://localhost:8000/api/organizations/<org_id>/invite/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"user_id": 2, "role": "MEMBER"}'
```

The API response will include an `email_sent` field indicating whether the email was sent successfully:

```json
{
  "id": 1,
  "user": {...},
  "organization": 1,
  "role": "MEMBER",
  "created_at": "2026-02-01T12:00:00Z",
  "email_sent": true
}
```

## Troubleshooting

### Common Issues

**1. Authentication Error (535)**

- Make sure you're using the App Password, not your regular Gmail password
- Verify 2-Step Verification is enabled on your Google account

**2. SMTPException: STARTTLS extension not supported**

- Verify `EMAIL_USE_TLS=True` in your `.env` file
- Check that `EMAIL_PORT=587` (not 465 or 25)

**3. Email not received**

- Check spam/junk folder
- Verify the recipient email address is correct
- Check Django console for error messages
- Verify Gmail account sending limits haven't been reached

**4. Connection Timeout**

- Check your firewall settings
- Verify port 587 is not blocked
- Try using port 465 with `EMAIL_USE_SSL=True` instead of TLS

### Development Mode - Console Backend

For development/testing without actually sending emails, you can use Django's console backend:

```python
# In settings.py (temporary)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

## Production Considerations

For production deployments, consider:

1. **Using a transactional email service** like:
   - SendGrid
   - Amazon SES
   - Mailgun
   - Postmark

2. **Rate limiting** to prevent spam
3. **Email queue** for handling bulk invitations
4. **Unsubscribe mechanism** for notification emails
5. **Email templates** stored in database for easy updates
6. **Proper error logging** and monitoring

## Security Notes

- Never commit your `.env` file with real credentials
- Use environment variables for all sensitive data
- Rotate app passwords periodically
- Monitor email sending for suspicious activity
- Implement rate limiting on invitation endpoints
