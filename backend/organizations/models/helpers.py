"""
Helper functions for organization permissions and user queries.
"""


def is_org_admin(user, organization):
    """
    Check if a user is an admin of the given organization.

    Args:
        user: User instance
        organization: Organization instance

    Returns:
        bool: True if user is an admin of the organization
    """
    from .organization_membership import OrganizationMembership

    if user.is_superuser:
        return True

    return OrganizationMembership.objects.filter(
        user=user, organization=organization, role=OrganizationMembership.Role.ORG_ADMIN
    ).exists()


def is_org_approved(organization):
    """
    Check if an organization is approved.

    Args:
        organization: Organization instance

    Returns:
        bool: True if organization is approved
    """
    return organization.is_approved()


def get_user_organizations(user):
    """
    Get all organizations a user belongs to.

    Args:
        user: User instance

    Returns:
        QuerySet of Organization instances
    """
    from .organization_membership import OrganizationMembership

    return OrganizationMembership.objects.filter(user=user).values_list(
        "organization", flat=True
    )


def is_user_org_admin(user, organization):
    """
    Check if the user is an admin of the specified organization.

    Args:
        user: User instance
        organization: Organization instance

    Returns:
        bool: True if user is an admin of the organization
    """
    return is_org_admin(user, organization)
