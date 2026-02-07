from rest_framework import serializers

from users.serializers.user_serializer import UserSerializer
from .models import (
    AIScreeningConfiguration,
    JobCategory,
    ExperienceLevel,
    JobProfile,
)
from organizations.serializers import OrganizationSerializer
from users.serializers import UserBasicSerializer


class AIScreeningConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for AI Screening Configuration"""

    class Meta:
        model = AIScreeningConfiguration
        fields = ["id", "title", "description"]
        read_only_fields = ["id", "title", "description"]


class JobCategorySerializer(serializers.ModelSerializer):
    """Serializer for Job Category"""

    class Meta:
        model = JobCategory
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


class ExperienceLevelSerializer(serializers.ModelSerializer):
    """Serializer for Experience Level"""

    class Meta:
        model = ExperienceLevel
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


class JobProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing job profiles"""

    category_name = serializers.CharField(source="category.title", read_only=True)
    experience_level_name = serializers.CharField(
        source="experience_level.title", read_only=True
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = JobProfile
        fields = [
            "id",
            "title",
            "organization",
            "organization_name",
            "category",
            "category_name",
            "employment_type",
            "experience_level",
            "experience_level_name",
            "created_by",
            "created_by_email",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class JobProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for job profile with all information"""

    organization = OrganizationSerializer(
        read_only=True,
    )
    category = JobCategorySerializer(read_only=True)
    experience_level = ExperienceLevelSerializer(read_only=True)
    ai_screening_configuration = AIScreeningConfigurationSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = JobProfile
        fields = [
            "id",
            "organization",
            "created_by",
            "title",
            "category",
            "employment_type",
            "experience_level",
            "description",
            "requirements",
            "skills",
            "ai_screening_configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        """Get creator's full name"""
        return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()


class JobProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating job profiles"""

    class Meta:
        model = JobProfile
        fields = [
            "title",
            "organization",
            "category",
            "employment_type",
            "experience_level",
            "description",
            "requirements",
            "skills",
            "ai_screening_configuration",
        ]
        read_only_fields = ["organization"]

    def create(self, validated_data):
        """Create job profile with organization from context"""
        # Organization must be passed via context, not in validated_data
        organization = self.context.get("organization")
        if not organization:
            raise serializers.ValidationError(
                {"organization": "Organization must be provided in context."}
            )

        # Validate organization is approved
        if not organization.is_approved():
            raise serializers.ValidationError(
                {
                    "organization": "Cannot create job profiles for non-approved organizations."
                }
            )

        return JobProfile.objects.create(organization=organization, **validated_data)

    def update(self, instance, validated_data):
        """Update job profile, explicitly excluding organization"""
        # Strip organization if somehow present in validated_data
        validated_data.pop("organization", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate_skills(self, value):
        """Validate skills array structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be an array.")

        for skill in value:
            if not isinstance(skill, dict):
                raise serializers.ValidationError(
                    "Each skill must be an object with 'skill' and 'is_required' fields."
                )
            if "skill" not in skill or "is_required" not in skill:
                raise serializers.ValidationError(
                    "Each skill must have 'skill' and 'is_required' fields."
                )
            if not isinstance(skill["skill"], str):
                raise serializers.ValidationError("Skill name must be a string.")
            if not isinstance(skill["is_required"], bool):
                raise serializers.ValidationError("is_required must be a boolean.")

        return value

    def validate_requirements(self, value):
        """Validate requirements array"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Requirements must be an array.")

        for requirement in value:
            if not isinstance(requirement, str):
                raise serializers.ValidationError("Each requirement must be a string.")

        return value
