from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .authentication import EmailTokenObtainPairView
from .views import (
    register_user,
    get_user_profile,
    update_user_profile,
    set_default_organization,
    password_reset_request,
    password_reset_confirm,
    upload_profile_picture,
    delete_profile_picture,
    delete_account,
)

# Decorate TokenRefreshView with Swagger documentation
decorated_token_refresh = swagger_auto_schema(
    method="post",
    operation_description="""Refresh an access token using a valid refresh token.
    
    When your access token expires, use this endpoint with your refresh token
    to obtain a new access token without requiring the user to log in again.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["refresh"],
        properties={
            "refresh": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="The refresh token obtained from login",
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description="Token refresh successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="New JWT access token (expires in 1 hour)",
                    ),
                    "refresh": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="New JWT refresh token (expires in 7 days, rotation enabled)",
                    ),
                },
            ),
        ),
        401: "Invalid or expired refresh token",
    },
    security=[],  # No authentication required for refresh
    tags=["Users"],
)(TokenRefreshView.as_view())

urlpatterns = [
    # Authentication endpoints
    path("auth/register/", register_user, name="register"),
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", decorated_token_refresh, name="token_refresh"),
    # User profile endpoints
    path("profile/", get_user_profile, name="user_profile"),
    path("profile/update/", update_user_profile, name="user_profile_update"),
    path(
        "profile/default-organization/",
        set_default_organization,
        name="set_default_organization",
    ),
    path(
        "profile/picture/",
        upload_profile_picture,
        name="upload_profile_picture",
    ),
    path(
        "profile/picture/delete/",
        delete_profile_picture,
        name="delete_profile_picture",
    ),
    path("profile/delete/", delete_account, name="delete_account"),
    # Password reset endpoints
    path("password-reset/", password_reset_request, name="password_reset_request"),
    path(
        "password-reset/confirm/", password_reset_confirm, name="password_reset_confirm"
    ),
]
