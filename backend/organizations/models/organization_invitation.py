import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings


class OrganizationInvitation(models.Model):
    """
    Invitation model for inviting users to join an organization.
    Invitations are single-use and have an expiration time.
    """

    class Role(models.TextChoices):
        ORG_ADMIN = "ORG_ADMIN", "Organization Admin"
        MEMBER = "MEMBER", "Member"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    token = models.CharField(max_length=64, unique=True, editable=False)
    invited_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, related_name="sent_invitations"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_invitations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        status = "Accepted" if self.accepted_at else "Pending"
        return f"{self.email} -> {self.organization.name} ({status})"

    def save(self, *args, **kwargs):
        """Generate token and set expiration on first save"""
        if not self.token:
            self.token = self._generate_token()
        if not self.expires_at:
            # Default expiration: 7 days from now
            expiration_days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
            self.expires_at = timezone.now() + timedelta(days=expiration_days)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(48)

    def is_valid(self):
        """Check if invitation is still valid (not expired and not accepted)"""
        return self.accepted_at is None and self.expires_at > timezone.now()

    def is_expired(self):
        """Check if invitation has expired"""
        return self.expires_at <= timezone.now()

    def accept(self):
        """Mark invitation as accepted"""
        self.accepted_at = timezone.now()
        self.save()
