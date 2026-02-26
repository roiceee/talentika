from rest_framework import serializers

from users.serializers.user_serializer import UserSerializer
from .models import (
    AIScreeningConfiguration,
    JobCategory,
    ExperienceLevel,
    JobProfile,
    Question,
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


class SkillItemSerializer(serializers.Serializer):
    """Represents a single skill entry in a job profile."""

    skill = serializers.CharField(
        help_text="Name of the skill, e.g. 'Python', 'Django'"
    )
    is_required = serializers.BooleanField(
        help_text="True if the skill is mandatory; False if nice-to-have"
    )


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "question_type",
            "order",
            "choices",
            "is_required",
        ]
        read_only_fields = []  # Allow id to be provided for updates

    def validate_choices(self, value):
        """Validate choices array for MCQ questions"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Choices must be an array.")

        for choice in value:
            if not isinstance(choice, str):
                raise serializers.ValidationError("Each choice must be a string.")

        return value

    def validate(self, attrs):
        """Validate that MCQ questions have choices"""
        question_type = attrs.get(
            "question_type", getattr(self.instance, "question_type", None)
        )
        choices = attrs.get("choices", getattr(self.instance, "choices", []))

        if (
            question_type
            in (
                Question.QuestionType.MCQ,
                Question.QuestionType.MCQ_SINGLE,
            )
            and not choices
        ):
            raise serializers.ValidationError(
                {"choices": "Multiple choice questions must have at least one choice."}
            )

        if question_type == Question.QuestionType.TEXT and choices:
            raise serializers.ValidationError(
                {"choices": "Text questions should not have choices."}
            )

        return attrs


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
    questions = QuestionSerializer(many=True, read_only=True)
    skills = SkillItemSerializer(many=True, read_only=True)

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
            "questions",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        """Get creator's full name"""
        return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()


class JobProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating job profiles"""

    questions = QuestionSerializer(many=True, required=False)
    skills = SkillItemSerializer(
        many=True,
        required=False,
        default=list,
        help_text="List of required/optional skills for this job profile",
    )

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
            "questions",
        ]
        read_only_fields = ["organization"]

    def create(self, validated_data):
        """Create job profile with organization from context and questions"""
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

        # Extract questions data
        questions_data = validated_data.pop("questions", [])

        # Create job profile
        job_profile = JobProfile.objects.create(
            organization=organization, **validated_data
        )

        # Create questions
        for question_data in questions_data:
            Question.objects.create(job_profile=job_profile, **question_data)

        return job_profile

    def update(self, instance, validated_data):
        """Update job profile, explicitly excluding organization, and update questions"""
        # Strip organization if somehow present in validated_data
        validated_data.pop("organization", None)

        # Extract questions data
        questions_data = validated_data.pop("questions", None)

        # Update job profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update questions if provided
        if questions_data is not None:
            # Get IDs of questions in the request
            question_ids_in_request = [
                q.get("id") for q in questions_data if q.get("id") is not None
            ]

            # Delete questions not in the request
            instance.questions.exclude(id__in=question_ids_in_request).delete()

            # Update or create questions
            for question_data in questions_data:
                question_id = question_data.get("id")
                if question_id:
                    # Update existing question
                    try:
                        question = instance.questions.get(id=question_id)
                        for attr, value in question_data.items():
                            if attr != "id":
                                setattr(question, attr, value)
                        question.save()
                    except Question.DoesNotExist:
                        # Question ID provided doesn't belong to this job profile
                        raise serializers.ValidationError(
                            {
                                "questions": f"Question with id {question_id} does not belong to this job profile."
                            }
                        )
                else:
                    # Create new question
                    Question.objects.create(job_profile=instance, **question_data)

        return instance

    def validate_requirements(self, value):
        """Validate requirements array"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Requirements must be an array.")

        for requirement in value:
            if not isinstance(requirement, str):
                raise serializers.ValidationError("Each requirement must be a string.")

        return value
