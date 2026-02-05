import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Uses email as the unique identifier for authentication.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class PasswordResetToken(models.Model):
    """
    Password reset token model for secure password resets.
    Tokens are single-use and have an expiration time.
    Similar to organization invitations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True, editable=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        status = "Used" if self.used_at else "Active"
        return f"Password reset for {self.user.email} ({status})"

    def save(self, *args, **kwargs):
        """Generate token and set expiration on first save"""
        if not self.token:
            self.token = self._generate_token()
        if not self.expires_at:
            # Default expiration: 24 hours from now
            expiration_hours = getattr(settings, "PASSWORD_RESET_EXPIRY_HOURS", 24)
            self.expires_at = timezone.now() + timedelta(hours=expiration_hours)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(48)

    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        return self.used_at is None and self.expires_at > timezone.now()

    def is_expired(self):
        """Check if token has expired"""
        return self.expires_at <= timezone.now()

    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.save()
