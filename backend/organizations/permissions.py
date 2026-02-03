"""
Permissions and utility functions for organization management.
"""

from rest_framework.permissions import BasePermission
from .models import is_org_admin, is_org_approved


class IsOrganizationAdmin(BasePermission):
    """
    Permission class to check if user is an admin of the organization.
    Expects 'org_id' in URL kwargs.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False

        from .models import Organization

        try:
            organization = Organization.objects.get(id=org_id)
            return is_org_admin(request.user, organization)
        except Organization.DoesNotExist:
            return False


class IsOrganizationMember(BasePermission):
    """
    Permission class to check if user is a member of the organization.
    Expects 'org_id' in URL kwargs.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False

        from .models import Organization

        try:
            organization = Organization.objects.get(id=org_id)
            return organization.memberships.filter(user=request.user).exists()
        except Organization.DoesNotExist:
            return False


class IsApprovedOrganization(BasePermission):
    """
    Permission class to check if organization is approved.
    Expects 'org_id' in URL kwargs.
    """

    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False

        from .models import Organization

        try:
            organization = Organization.objects.get(id=org_id)
            return is_org_approved(organization)
        except Organization.DoesNotExist:
            return False


class IsSuperAdmin(BasePermission):
    """
    Permission class to check if user is a super admin.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


# Utility functions for common checks
def can_access_organization_feature(user, organization):
    """
    Check if user can access protected organization features.
    User must be a member and organization must be approved.

    Args:
        user: User instance
        organization: Organization instance

    Returns:
        tuple: (can_access: bool, reason: str)
    """
    if user.is_superuser:
        return True, "Super admin access"

    # Check if user is a member
    if not organization.memberships.filter(user=user).exists():
        return False, "User is not a member of this organization"

    # Check if organization is approved
    if not is_org_approved(organization):
        return False, f"Organization is {organization.get_status_display()}"

    return True, "Access granted"


def get_user_role_in_organization(user, organization):
    """
    Get the user's role in an organization.

    Args:
        user: User instance
        organization: Organization instance

    Returns:
        str or None: Role name or None if not a member
    """
    try:
        membership = organization.memberships.get(user=user)
        return membership.role
    except:
        return None


class IsOrgAdminOfOwnOrganization(BasePermission):
    """
    Permission class to check if user is an admin of at least one organization.
    Used for creating invitations - requires org_id in request data.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # User must have at least one organization membership with admin role
        from .models import OrganizationMembership

        return OrganizationMembership.objects.filter(
            user=request.user, role=OrganizationMembership.Role.ORG_ADMIN
        ).exists()
