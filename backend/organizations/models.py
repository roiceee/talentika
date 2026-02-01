from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Uses email as the unique identifier for authentication.
    """

    email = models.EmailField(unique=True, blank=False)
    # first_name, last_name, password are inherited from AbstractUser
    # is_superuser is also inherited for app owner/super admin access

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"


class Organization(models.Model):
    """
    Organization model representing companies/teams that users belong to.
    Organizations must be approved by super admins before becoming active.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_organizations",
    )

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def is_approved(self):
        """Check if organization is approved"""
        return self.status == self.Status.APPROVED

    def can_invite_users(self):
        """Check if organization can invite users (only approved orgs)"""
        return self.is_approved()

    def approve(self, approved_by_user):
        """Approve the organization"""
        self.status = self.Status.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = approved_by_user
        self.save()

    def reject(self):
        """Reject the organization"""
        self.status = self.Status.REJECTED
        self.save()

    def suspend(self):
        """Suspend the organization"""
        self.status = self.Status.SUSPENDED
        self.save()


class OrganizationMembership(models.Model):
    """
    Many-to-many relationship between Users and Organizations with role information.
    """

    class Role(models.TextChoices):
        ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
        MEMBER = "MEMBER", "Member"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organization_memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_memberships"
        unique_together = [["user", "organization"]]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
        )

    def is_admin(self):
        """Check if this membership has admin role"""
        return self.role == self.Role.ORG_ADMIN


# Permission helper functions
def is_org_admin(user, organization):
    """
    Check if a user is an admin of the given organization.

    Args:
        user: User instance
        organization: Organization instance

    Returns:
        bool: True if user is an admin of the organization
    """
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


def get_user_organizations(user, status=None):
    """
    Get all organizations a user belongs to, optionally filtered by status.

    Args:
        user: User instance
        status: Optional organization status to filter by

    Returns:
        QuerySet of Organization instances
    """
    queryset = Organization.objects.filter(memberships__user=user)
    if status:
        queryset = queryset.filter(status=status)
    return queryset.distinct()


def get_user_admin_organizations(user):
    """
    Get all organizations where the user is an admin.

    Args:
        user: User instance

    Returns:
        QuerySet of Organization instances
    """
    return Organization.objects.filter(
        memberships__user=user, memberships__role=OrganizationMembership.Role.ORG_ADMIN
    ).distinct()
