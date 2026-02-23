from rest_framework import serializers

from .models import ApplicationAnalysis


class ApplicationAnalysisSerializer(serializers.ModelSerializer):
    """Read-only serializer for the full analysis result."""

    class Meta:
        model = ApplicationAnalysis
        fields = [
            "id",
            "job_application",
            "status",
            "error_message",
            "extracted_resume_text",
            "ai_analysis_summary",
            "notable_traits",
            "key_skills",
            "score",
            "detailed_analysis",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ApplicationAnalysisStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer — status + score only."""

    class Meta:
        model = ApplicationAnalysis
        fields = [
            "id",
            "job_application",
            "status",
            "score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ApplicationAnalysisListItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the org-level list endpoint.

    Includes flattened applicant and job-profile info so callers don't need
    secondary requests.
    """

    # Applicant fields (from the related JobApplication)
    applicant_id = serializers.UUIDField(source="job_application.id", read_only=True)
    applicant_first_name = serializers.CharField(
        source="job_application.first_name", read_only=True
    )
    applicant_last_name = serializers.CharField(
        source="job_application.last_name", read_only=True
    )
    applicant_email = serializers.EmailField(
        source="job_application.email", read_only=True
    )
    applicant_phone = serializers.CharField(
        source="job_application.phone", read_only=True
    )
    job_application_status = serializers.CharField(
        source="job_application.status", read_only=True
    )

    # Job profile fields
    job_profile_id = serializers.UUIDField(
        source="job_application.job_profile.id", read_only=True
    )
    job_profile_title = serializers.CharField(
        source="job_application.job_profile.title", read_only=True
    )

    # Job application fields
    job_application_id = serializers.UUIDField(
        source="job_application.id", read_only=True
    )

    class Meta:
        model = ApplicationAnalysis
        fields = [
            "id",
            "applicant_id",
            "applicant_first_name",
            "applicant_last_name",
            "applicant_email",
            "applicant_phone",
            "job_application_status",
            "job_profile_id",
            "job_profile_title",
            "job_application_id",
            "status",
            "score",
            "ai_analysis_summary",
            "notable_traits",
            "key_skills",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
