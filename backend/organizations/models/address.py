import uuid
from django.db import models


class Address(models.Model):
    """
    Address model for storing reusable addresses.
    Can be linked to various entities like users, organizations, orders, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line1 = models.CharField(max_length=255, help_text="Street address line 1")
    line2 = models.CharField(
        max_length=255, blank=True, help_text="Street address line 2 (optional)"
    )
    city = models.CharField(max_length=100, db_index=True)
    province_state = models.CharField(
        max_length=100, help_text="Province, state, or region"
    )
    postal_code = models.CharField(max_length=20)
    country = models.CharField(
        max_length=2, db_index=True, help_text="ISO 3166-1 alpha-2 country code"
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "addresses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "country"]),
            models.Index(fields=["country", "province_state"]),
        ]
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.line1}, {self.city}, {self.country}"

    def get_full_address(self):
        """Get the complete formatted address"""
        parts = [self.line1]
        if self.line2:
            parts.append(self.line2)
        parts.extend([self.city, self.province_state, self.postal_code, self.country])
        return ", ".join(parts)
