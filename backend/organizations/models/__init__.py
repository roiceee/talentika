"""
Django models for the organizations app.

This package contains all models related to organizations, memberships, and addresses.
User model is now in the users app.
"""

# Import all models to make them available when importing from organizations.models
from users.models import User
from .address import Address
from .organization import Organization
from .organization_membership import OrganizationMembership
from .organization_invitation import OrganizationInvitation

# Import helper functions
from .helpers import (
    is_org_admin,
    is_org_approved,
    get_user_organizations,
    is_user_org_admin,
)

__all__ = [
    # Models
    "User",
    "Address",
    "Organization",
    "OrganizationMembership",
    "OrganizationInvitation",
    # Helper functions
    "is_org_admin",
    "is_org_approved",
    "get_user_organizations",
    "is_user_org_admin",
]
