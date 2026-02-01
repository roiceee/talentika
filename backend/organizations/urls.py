from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .authentication import EmailTokenObtainPairView

urlpatterns = [
    # Authentication
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # User registration
    path("register/", views.register_user, name="register-user"),
    # Organization management
    path("organizations/", views.list_user_organizations, name="list-organizations"),
    path(
        "organizations/create/", views.create_organization, name="create-organization"
    ),
    path(
        "organizations/<int:org_id>/", views.get_organization, name="get-organization"
    ),
    path(
        "organizations/<int:org_id>/update/",
        views.update_organization,
        name="update-organization",
    ),
    # Organization members
    path(
        "organizations/<int:org_id>/members/",
        views.list_organization_members,
        name="list-members",
    ),
    path(
        "organizations/<int:org_id>/invite/",
        views.invite_user_to_organization,
        name="invite-user",
    ),
    # Admin endpoints
    path(
        "admin/organizations/pending/",
        views.list_pending_organizations,
        name="list-pending-organizations",
    ),
    path(
        "admin/organizations/<int:org_id>/status/",
        views.manage_organization_status,
        name="manage-organization-status",
    ),
]
