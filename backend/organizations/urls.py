from django.urls import path
from .views import (
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
    upload_org_profile_picture,
    delete_org_profile_picture,
)


urlpatterns = [
    # Organization management
    path("organizations/", list_user_organizations, name="list-organizations"),
    path("organizations/create/", create_organization, name="create-organization"),
    path("organizations/<uuid:org_id>/", get_organization, name="get-organization"),
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
    # Profile picture
    path(
        "organizations/<uuid:org_id>/profile-picture/",
        upload_org_profile_picture,
        name="upload-org-profile-picture",
    ),
    path(
        "organizations/<uuid:org_id>/profile-picture/delete/",
        delete_org_profile_picture,
        name="delete-org-profile-picture",
    ),
]
