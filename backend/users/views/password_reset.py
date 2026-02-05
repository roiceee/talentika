from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings

from users.models import User, PasswordResetToken
from ..serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer


@swagger_auto_schema(
    method="post",
    operation_description="""
    Request a password reset link.
    
    Sends an email with a password reset link containing a secure token.
    The token is valid for a limited time (default: 24 hours).
    
    This is a public endpoint - no authentication required.
    For security, the response is the same whether the email exists or not.
    """,
    request_body=PasswordResetRequestSerializer,
    responses={
        200: openapi.Response(
            "Password reset email sent (if email exists)",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Success message",
                    )
                },
            ),
        ),
        400: "Invalid data",
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request a password reset link via email.

    Sends a password reset email with a secure token if the email exists.
    The email contains a link that the user can use to reset their password.
    For security, the response is always the same whether the email exists or not.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]

        # Try to get user - don't reveal if email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success anyway for security
            return Response(
                {
                    "message": "If an account with that email exists, a password reset link has been sent."
                },
                status=status.HTTP_200_OK,
            )

        try:
            # Create password reset token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Construct reset URL (frontend will handle this)
            reset_url = f"{settings.FRONTEND_URL}/password-reset/{reset_token.token}/"

            # Send email
            subject = "Password Reset Request - Talentika"
            message = f"""
Hello {user.first_name},

You requested to reset your password for your Talentika account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this password reset, please ignore this email.

Best regards,
Talentika Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but still return success to user for security
            pass

        return Response(
            {
                "message": "If an account with that email exists, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Confirm password reset with token.
    
    Uses the token from the password reset email to set a new password.
    The token is validated and must not be expired or already used.
    
    Required fields:
    - token: Reset token from the reset link
    - new_password: The new password (minimum 8 characters)
    - new_password_confirm: Confirmation of the new password
    """,
    request_body=PasswordResetConfirmSerializer,
    responses={
        200: openapi.Response(
            "Password reset successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Success message",
                    )
                },
            ),
        ),
        400: "Validation error or invalid token",
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset and set new password.

    Validates the reset token and uid, then sets the new password for the user.
    After successful reset, the user can login with their new password.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Password has been reset successfully. You can now login with your new password."
            },
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
