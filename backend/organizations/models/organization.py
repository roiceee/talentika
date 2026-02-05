import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations",
        help_text="Physical address of the organization",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
