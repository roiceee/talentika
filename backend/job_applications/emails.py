"""
Email utilities for job application notifications.
"""

import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_application_confirmation_email(job_application):
    """
    Send a confirmation email to the applicant after they submit a job application.
    """
    frontend_url = settings.FRONTEND_WEB_URL
    job_profile = job_application.job_profile
    organization = job_profile.organization

    subject = f"Application Received – {job_profile.title} at {organization.name}"

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .container {{ background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #2563eb; margin: 0; font-size: 24px; }}
            .content {{ margin-bottom: 30px; }}
            .content p {{ margin: 10px 0; }}
            .highlight {{ background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Application Received</h1>
            </div>
            <div class="content">
                <p>Hi <strong>{job_application.first_name} {job_application.last_name}</strong>,</p>
                <p>Thank you for applying! We've received your application and it's currently under review.</p>
                <div class="highlight">
                    <p><strong>Position:</strong> {job_profile.title}</p>
                    <p><strong>Organization:</strong> {organization.name}</p>
                    <p><strong>Application ID:</strong> {job_application.id}</p>
                </div>
                <p>The hiring team will review your application and reach out to you if your profile matches their requirements.</p>
                <p>We appreciate your interest and wish you the best of luck!</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Talentika.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
Hi {job_application.first_name} {job_application.last_name},

Thank you for applying! We've received your application and it's currently under review.

Position: {job_profile.title}
Organization: {organization.name}
Application ID: {job_application.id}

The hiring team will review your application and reach out to you if your profile matches their requirements.

We appreciate your interest and wish you the best of luck!

---
This is an automated message from Talentika.
Please do not reply to this email.
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[job_application.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception(
            "Failed to send application confirmation email to %s", job_application.email
        )
        return False
