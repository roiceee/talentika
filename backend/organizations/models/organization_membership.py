import uuid
from django.db import models
from django.conf import settings


class OrganizationMembership(models.Model):
    """
    Many-to-many relationship between Users and Organizations with role information.
    """

    class Role(models.TextChoices):
        ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
        MEMBER = "MEMBER", "Member"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_memberships"
        ordering = ["-created_at"]
        unique_together = [("user", "organization")]  # User can't join same org twice

    def __str__(self):
        return (
            f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
        )

    def is_admin(self):
        """Check if this membership has admin role"""
        return self.role == self.Role.ORG_ADMIN
