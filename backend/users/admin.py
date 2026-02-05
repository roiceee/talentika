from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with email as primary identifier"""

    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token_preview", "created_at", "expires_at", "is_used"]
    list_filter = ["created_at", "expires_at", "used_at"]
    search_fields = ["user__email", "token"]
    readonly_fields = ["token", "created_at"]
    ordering = ["-created_at"]

    def token_preview(self, obj):
        return f"{obj.token[:20]}..."

    token_preview.short_description = "Token"

    def is_used(self, obj):
        return obj.used_at is not None

    is_used.boolean = True
    is_used.short_description = "Used"
