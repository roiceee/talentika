from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, Organization, OrganizationMembership


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


class OrganizationMembershipInline(admin.TabularInline):
    """Inline display of organization members"""

    model = OrganizationMembership
    extra = 0
    readonly_fields = ["created_at"]
    autocomplete_fields = ["user"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization admin with approve/reject actions.
    Shows status with color coding and provides bulk approval/rejection.
    """

    list_display = [
        "name",
        "status_badge",
        "created_at",
        "approved_at",
        "approved_by",
        "member_count",
    ]
    list_filter = ["status", "created_at", "approved_at"]
    search_fields = ["name", "address"]
    readonly_fields = ["created_at", "approved_at", "approved_by"]
    inlines = [OrganizationMembershipInline]

    fieldsets = (
        ("Organization Information", {"fields": ("name", "address")}),
        ("Status", {"fields": ("status", "approved_at", "approved_by")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    actions = ["approve_organizations", "reject_organizations", "suspend_organizations"]

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            Organization.Status.PENDING: "#FFA500",  # Orange
            Organization.Status.APPROVED: "#28A745",  # Green
            Organization.Status.REJECTED: "#DC3545",  # Red
            Organization.Status.SUSPENDED: "#6C757D",  # Gray
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def member_count(self, obj):
        """Display number of members"""
        return obj.memberships.count()

    member_count.short_description = "Members"

    def approve_organizations(self, request, queryset):
        """Bulk approve selected organizations"""
        pending_orgs = queryset.filter(status=Organization.Status.PENDING)
        count = 0
        for org in pending_orgs:
            org.approve(request.user)
            count += 1

        self.message_user(request, f"{count} organization(s) approved successfully.")

    approve_organizations.short_description = "Approve selected organizations"

    def reject_organizations(self, request, queryset):
        """Bulk reject selected organizations"""
        pending_orgs = queryset.filter(status=Organization.Status.PENDING)
        count = pending_orgs.count()
        pending_orgs.update(status=Organization.Status.REJECTED)

        self.message_user(request, f"{count} organization(s) rejected.")

    reject_organizations.short_description = "Reject selected organizations"

    def suspend_organizations(self, request, queryset):
        """Bulk suspend selected organizations"""
        approved_orgs = queryset.filter(status=Organization.Status.APPROVED)
        count = approved_orgs.count()
        approved_orgs.update(status=Organization.Status.SUSPENDED)

        # TODO: Send notification emails to organization admins about suspension

        self.message_user(request, f"{count} organization(s) suspended.")

    suspend_organizations.short_description = "Suspend selected organizations"


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Organization membership admin for managing user-org relationships"""

    list_display = ["user", "organization", "role", "created_at"]
    list_filter = ["role", "created_at", "organization__status"]
    search_fields = ["user__email", "user__username", "organization__name"]
    autocomplete_fields = ["user", "organization"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Membership Information", {"fields": ("user", "organization", "role")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
