from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .views import (
    register_user,
    list_user_organizations,
    create_organization,
    get_organization,
    update_organization,
    list_organization_members,
    remove_member,
    leave_organization,
    create_invitation,
    list_organization_invitations,
    validate_invitation,
    accept_invitation,
)
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
    path("register/", register_user, name="register-user"),
    # Organization management
    path("organizations/", list_user_organizations, name="list-organizations"),
    path(
        "organizations/create/", create_organization, name="create-organization"
    ),
    path(
        "organizations/<uuid:org_id>/", get_organization, name="get-organization"
    ),
    path(
        "organizations/<uuid:org_id>/update/",
        update_organization,
        name="update-organization",
    ),
    # Organization members
    path(
        "organizations/<uuid:org_id>/members/",
        list_organization_members,
        name="list-members",
    ),
    path(
        "organizations/<uuid:org_id>/members/<uuid:membership_id>/",
        remove_member,
        name="remove-member",
    ),
    path(
        "organizations/<uuid:org_id>/leave/",
        leave_organization,
        name="leave-organization",
    ),
    # Invitation endpoints
    path(
        "organizations/<uuid:org_id>/invitations/",
        create_invitation,
        name="create-invitation",
    ),
    path(
        "organizations/<uuid:org_id>/invitations/list/",
        list_organization_invitations,
        name="list-invitations",
    ),
    path(
        "invitations/validate/",
        validate_invitation,
        name="validate-invitation",
    ),
    path("invitations/accept/", accept_invitation, name="accept-invitation"),
]
