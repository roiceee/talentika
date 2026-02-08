from django.contrib import admin
from .models import (
    JobApplication,
    ApplicantAddress,
    QuestionAnswer,
    ApplicationAttachment,
)


class ApplicantAddressInline(admin.StackedInline):
    model = ApplicantAddress
    extra = 0


class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswer
    extra = 0
    readonly_fields = ["question", "answer_text", "selected_choices", "created_at"]


class ApplicationAttachmentInline(admin.TabularInline):
    model = ApplicationAttachment
    extra = 0
    readonly_fields = ["file_name", "file_type", "file_size", "uploaded_at"]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "email",
        "phone",
        "job_profile",
        "status",
        "submitted_at",
    ]
    list_filter = ["status", "job_profile__organization", "submitted_at"]
    search_fields = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "job_profile__title",
    ]
    readonly_fields = ["id", "submitted_at", "created_at", "updated_at"]
    inlines = [
        ApplicantAddressInline,
        QuestionAnswerInline,
        ApplicationAttachmentInline,
    ]
    autocomplete_fields = ["job_profile"]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    full_name.short_description = "Applicant Name"


@admin.register(ApplicantAddress)
class ApplicantAddressAdmin(admin.ModelAdmin):
    list_display = ["job_application", "city", "province_state", "country"]
    search_fields = [
        "job_application__first_name",
        "job_application__last_name",
        "city",
        "province_state",
        "country",
    ]
    readonly_fields = ["id"]


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ["job_application", "question_preview", "created_at"]
    search_fields = [
        "job_application__first_name",
        "job_application__last_name",
        "question__text",
    ]
    readonly_fields = ["id", "created_at"]
    autocomplete_fields = ["job_application", "question"]

    def question_preview(self, obj):
        return (
            obj.question.text[:50] + "..."
            if len(obj.question.text) > 50
            else obj.question.text
        )

    question_preview.short_description = "Question"


@admin.register(ApplicationAttachment)
class ApplicationAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "file_type",
        "job_application",
        "file_size_kb",
        "uploaded_at",
    ]
    list_filter = ["file_type", "uploaded_at"]
    search_fields = [
        "file_name",
        "job_application__first_name",
        "job_application__last_name",
    ]
    readonly_fields = ["id", "uploaded_at"]
    autocomplete_fields = ["job_application"]

    def file_size_kb(self, obj):
        return f"{obj.file_size / 1024:.2f} KB"

    file_size_kb.short_description = "File Size"
