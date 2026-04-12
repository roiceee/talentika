from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from django.db.models import Count

from users.serializers.user_serializer import UserSerializer
from .models import (
    JobCategory,
    ExperienceLevel,
    JobProfile,
    Qualification,
    Question,
)
from organizations.serializers import OrganizationSerializer
from users.serializers import UserBasicSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


class ExperienceLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceLevel
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


# ─── Qualification serializers ───────────────────────────────────────────────


class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = [
            "id",
            "category",
            "name",
            "requirement_level",
            "years_required",
            "proficiency_level",
            "order",
        ]
        read_only_fields = ["id"]


class QualificationWriteSerializer(serializers.Serializer):
    """Used for create/update — accepts optional id for upserts."""

    id = serializers.UUIDField(required=False)
    category = serializers.ChoiceField(choices=Qualification.Category.choices)
    name = serializers.CharField(max_length=255)
    requirement_level = serializers.ChoiceField(
        choices=Qualification.RequirementLevel.choices,
        default="required",
    )
    years_required = serializers.IntegerField(
        required=False, allow_null=True, default=None
    )
    proficiency_level = serializers.ChoiceField(
        choices=Qualification.ProficiencyLevel.choices,
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None,
    )
    order = serializers.IntegerField(default=0)


# ─── Question serializers ───────────────────────────────────────────────────


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
        read_only_fields = []

    def validate_choices(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Choices must be an array.")
        for choice in value:
            if not isinstance(choice, str):
                raise serializers.ValidationError("Each choice must be a string.")
        return value

    def validate(self, attrs):
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


# ─── Job profile serializers ────────────────────────────────────────────────


class JobProfileListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.title", read_only=True)
    experience_level_name = serializers.CharField(
        source="experience_level.title", read_only=True
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    application_count = serializers.SerializerMethodField()
    application_status_counts = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_application_count(self, obj):
        return obj.applications.count()

    @swagger_serializer_method(serializer_or_field=serializers.DictField(child=serializers.IntegerField()))
    def get_application_status_counts(self, obj):
        rows = obj.applications.values("status").annotate(count=Count("id"))
        return {row["status"]: row["count"] for row in rows}

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
            "is_active",
            "created_at",
            "application_count",
            "application_status_counts",
        ]
        read_only_fields = ["id", "created_at"]


class JobProfileDetailSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    experience_level = ExperienceLevelSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    qualifications = QualificationSerializer(many=True, read_only=True)
    application_count = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField())
    def get_application_count(self, obj):
        return obj.applications.count()

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
            "qualifications",
            "questions",
            "is_active",
            "application_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "application_count",
        ]


class JobProfileCreateSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    qualifications = QualificationWriteSerializer(many=True, required=False)

    class Meta:
        model = JobProfile
        fields = [
            "title",
            "organization",
            "category",
            "employment_type",
            "experience_level",
            "description",
            "qualifications",
            "questions",
            "is_active",
        ]
        read_only_fields = ["organization"]

    def _sync_qualifications(self, job_profile, qualifications_data):
        """Replace-all sync for qualifications."""
        existing_ids = set(job_profile.qualifications.values_list("id", flat=True))
        incoming_ids = set()

        for idx, q_data in enumerate(qualifications_data):
            q_id = q_data.get("id")
            defaults = {
                "category": q_data["category"],
                "name": q_data["name"],
                "requirement_level": q_data.get("requirement_level", "required"),
                "years_required": q_data.get("years_required"),
                "proficiency_level": q_data.get("proficiency_level") or None,
                "order": q_data.get("order", idx),
            }
            if q_id:
                Qualification.objects.update_or_create(
                    id=q_id, job_profile=job_profile, defaults=defaults
                )
                incoming_ids.add(q_id)
            else:
                obj = Qualification.objects.create(job_profile=job_profile, **defaults)
                incoming_ids.add(obj.id)

        # Delete removed qualifications
        to_delete = existing_ids - incoming_ids
        if to_delete:
            Qualification.objects.filter(
                id__in=to_delete, job_profile=job_profile
            ).delete()

    def _sync_questions(self, job_profile, questions_data):
        """Replace-all sync for questions."""
        existing_ids = set(job_profile.questions.values_list("id", flat=True))
        incoming_ids = set()

        for idx, q_data in enumerate(questions_data):
            q_id = q_data.get("id")
            defaults = {
                "text": q_data["text"],
                "question_type": q_data.get("question_type", "text"),
                "order": q_data.get("order", idx),
                "choices": q_data.get("choices", []),
                "is_required": q_data.get("is_required", True),
            }
            if q_id:
                Question.objects.update_or_create(
                    id=q_id, job_profile=job_profile, defaults=defaults
                )
                incoming_ids.add(q_id)
            else:
                obj = Question.objects.create(job_profile=job_profile, **defaults)
                incoming_ids.add(obj.id)

        to_delete = existing_ids - incoming_ids
        if to_delete:
            Question.objects.filter(id__in=to_delete, job_profile=job_profile).delete()

    def create(self, validated_data):
        organization = self.context.get("organization")
        if not organization:
            raise serializers.ValidationError(
                {"organization": "Organization must be provided in context."}
            )

        if not organization.is_approved():
            raise serializers.ValidationError(
                {
                    "organization": "Cannot create job profiles for non-approved organizations."
                }
            )

        questions_data = validated_data.pop("questions", [])
        qualifications_data = validated_data.pop("qualifications", [])

        job_profile = JobProfile.objects.create(
            organization=organization, **validated_data
        )

        self._sync_qualifications(job_profile, qualifications_data)
        self._sync_questions(job_profile, questions_data)

        return job_profile

    def update(self, instance, validated_data):
        validated_data.pop("organization", None)

        questions_data = validated_data.pop("questions", None)
        qualifications_data = validated_data.pop("qualifications", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if qualifications_data is not None:
            self._sync_qualifications(instance, qualifications_data)

        if questions_data is not None:
            self._sync_questions(instance, questions_data)

        return instance
