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
    frontend_url = settings.FRONTEND_WEB_URL

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


def send_invitation_token_email(invitation):
    """
    Send an invitation email with a secure token link.
    The link points to the frontend which will call the API to validate and accept.

    Args:
        invitation: OrganizationInvitation instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Get frontend URL from settings (with fallback)
    frontend_url = settings.FRONTEND_WEB_URL

    # Construct invitation acceptance URL (front-end URL with token)
    invitation_url = f"{frontend_url}/invite/accept?token={invitation.token}"

    subject = f"You've been invited to join {invitation.organization.name} on Talentika"

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
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 12px;
                margin: 20px 0;
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
                <h1>🎉 You're Invited!</h1>
            </div>
            
            <div class="content">
                <p>Hello <strong>{invitation.email}</strong>,</p>
                
                <p>You've been invited to join an organization on Talentika.</p>
                
                <div class="highlight">
                    <p><strong>Organization:</strong> {invitation.organization.name}</p>
                    <p><strong>Role:</strong> {invitation.get_role_display()}</p>
                    <p><strong>Invited by:</strong> {invitation.invited_by.get_full_name()} ({invitation.invited_by.email})</p>
                    <p><strong>Expires:</strong> {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>To accept this invitation, click the button below:</p>
                
                <center>
                    <a href="{invitation_url}" class="button">Accept Invitation</a>
                </center>
                
                <div class="warning">
                    <p><strong>⚠️ Important:</strong></p>
                    <ul>
                        <li>This invitation link is single-use and expires on {invitation.expires_at.strftime('%B %d, %Y')}</li>
                        <li>You'll need to sign in or create an account with this email address</li>
                        <li>You can only belong to one organization at a time</li>
                    </ul>
                </div>
                
                <p>If you don't have an account yet, you'll be able to create one during the acceptance process.</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from Talentika.</p>
                <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                <p>The invitation link cannot be used by anyone else.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create plain text version
    plain_message = f"""
    Hello {invitation.email},

    You've been invited to join {invitation.organization.name} on Talentika!

    Organization: {invitation.organization.name}
    Role: {invitation.get_role_display()}
    Invited by: {invitation.invited_by.get_full_name()} ({invitation.invited_by.email})
    Expires: {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}

    To accept this invitation, click the link below:
    {invitation_url}

    IMPORTANT:
    - This invitation link is single-use and expires on {invitation.expires_at.strftime('%B %d, %Y')}
    - You'll need to sign in or create an account with this email address
    - You can only belong to one organization at a time

    If you don't have an account yet, you'll be able to create one during the acceptance process.

    ---
    This is an automated message from Talentika.
    If you didn't expect this invitation, you can safely ignore this email.
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # TODO: Implement proper logging in production
        print(f"Failed to send invitation email: {str(e)}")
        return False
