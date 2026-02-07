from django.contrib import admin
from .models import (
    AIScreeningConfiguration,
    JobCategory,
    ExperienceLevel,
    JobProfile,
    Question,
)


@admin.register(AIScreeningConfiguration)
class AIScreeningConfigurationAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at", "updated_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ExperienceLevel)
class ExperienceLevelAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(JobProfile)
class JobProfileAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "organization",
        "category",
        "employment_type",
        "experience_level",
        "created_by",
        "created_at",
    ]
    list_filter = ["employment_type", "category", "experience_level", "organization"]
    search_fields = ["title", "description", "organization__name", "created_by__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = [
        "category",
        "experience_level",
        "ai_screening_configuration",
        "organization",
        "created_by",
    ]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "text_preview",
        "job_profile",
        "question_type",
        "order",
        "is_required",
        "created_at",
    ]
    list_filter = ["question_type", "is_required", "job_profile__organization"]
    search_fields = ["text", "job_profile__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["job_profile"]
    ordering = ["job_profile", "order"]

    def text_preview(self, obj):
        """Show first 50 characters of question text"""
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Question"
