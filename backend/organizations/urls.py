from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from . import views
from .authentication import EmailTokenObtainPairView

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
    tags=["Authentication"],
)(TokenRefreshView.as_view())

urlpatterns = [
    # Authentication
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/refresh/", decorated_token_refresh, name="token-refresh"),
    # User registration
    path("register/", views.register_user, name="register-user"),
    # Organization management
    path("organizations/", views.list_user_organizations, name="list-organizations"),
    path(
        "organizations/create/", views.create_organization, name="create-organization"
    ),
    path(
        "organizations/<uuid:org_id>/", views.get_organization, name="get-organization"
    ),
    path(
        "organizations/<uuid:org_id>/update/",
        views.update_organization,
        name="update-organization",
    ),
    # Organization members
    path(
        "organizations/<uuid:org_id>/members/",
        views.list_organization_members,
        name="list-members",
    ),
    # Invitation endpoints
    path(
        "organizations/<uuid:org_id>/invitations/",
        views.create_invitation,
        name="create-invitation",
    ),
    path(
        "invitations/validate/",
        views.validate_invitation,
        name="validate-invitation",
    ),
    path("invitations/accept/", views.accept_invitation, name="accept-invitation"),
]
