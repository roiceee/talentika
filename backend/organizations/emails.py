"""
Email utilities for organization invitations and notifications.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_invitation_email(invited_user, organization, invited_by):
    """
    Send an invitation email to a user who has been invited to join an organization.

    Args:
        invited_user: User instance who is being invited
        organization: Organization instance they're being invited to
        invited_by: User instance who sent the invitation
    """
    frontend_url = settings.FRONTEND_URL

    subject = f"You've been invited to join {organization.name} on Talentika"

    # Create HTML email content
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2563eb;
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                margin-bottom: 30px;
            }}
            .content p {{
                margin: 10px 0;
            }}
            .highlight {{
                background-color: #f3f4f6;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                background-color: #2563eb;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-weight: 600;
                margin: 20px 0;
            }}
            .button:hover {{
                background-color: #1d4ed8;
            }}
            .footer {{
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Organization Invitation</h1>
            </div>
            
            <div class="content">
                <p>Hello <strong>{invited_user.get_full_name() or invited_user.email}</strong>,</p>
                
                <p>Great news! You've been invited to join an organization on Talentika.</p>
                
                <div class="highlight">
                    <p><strong>Organization:</strong> {organization.name}</p>
                    <p><strong>Invited by:</strong> {invited_by.get_full_name()} ({invited_by.email})</p>
                </div>
                
                <p>Click the button below to access your organization dashboard and start collaborating with your team:</p>
                
                <center>
                    <a href="{frontend_url}" class="button">Go to Talentika</a>
                </center>
                
                <p>Once you log in, you'll have access to all organization features and can start working with your team members.</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from Talentika.</p>
                <p>If you didn't expect this invitation, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create plain text version for email clients that don't support HTML
    plain_message = f"""
    Hello {invited_user.get_full_name() or invited_user.email},

    You've been invited to join {organization.name} on Talentika!

    Invited by: {invited_by.get_full_name()} ({invited_by.email})

    Click the link below to access your organization:
    {frontend_url}

    Once you log in, you'll have access to all organization features and can start working with your team members.

    ---
    This is an automated message from Talentika.
    If you didn't expect this invitation, you can safely ignore this email.
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invited_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Failed to send invitation email: {str(e)}")
        return False
