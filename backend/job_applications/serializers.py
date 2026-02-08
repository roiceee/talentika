from rest_framework import serializers
from .models import (
    JobApplication,
    ApplicantAddress,
    QuestionAnswer,
    ApplicationAttachment,
)
from job_profile.models import Question


class ApplicantAddressSerializer(serializers.ModelSerializer):
    """Serializer for applicant address"""

    class Meta:
        model = ApplicantAddress
        fields = [
            "line1",
            "line2",
            "city",
            "province_state",
            "postal_code",
            "country",
        ]

    def validate_country(self, value):
        """Validate country code is 2 characters"""
        if len(value) != 2:
            raise serializers.ValidationError(
                "Country code must be 2 characters (ISO 3166-1 alpha-2)."
            )
        return value.upper()


class QuestionAnswerSerializer(serializers.ModelSerializer):
    """Serializer for question answers"""

    class Meta:
        model = QuestionAnswer
        fields = ["question", "answer_text", "selected_choices"]

    def validate(self, attrs):
        """Validate answer based on question type"""
        question_id = attrs.get("question")

        try:
            question = Question.objects.get(
                id=question_id.id if hasattr(question_id, "id") else question_id
            )
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question": "Question does not exist."})

        answer_text = attrs.get("answer_text", "")
        selected_choices = attrs.get("selected_choices", [])

        # Check if required question is answered
        if question.is_required:
            if question.question_type == Question.QuestionType.TEXT and not answer_text:
                raise serializers.ValidationError(
                    {"answer_text": f"Answer is required for question: {question.text}"}
                )
            if (
                question.question_type == Question.QuestionType.MCQ
                and not selected_choices
            ):
                raise serializers.ValidationError(
                    {
                        "selected_choices": f"Answer is required for question: {question.text}"
                    }
                )

        # Validate based on question type
        if question.question_type == Question.QuestionType.TEXT:
            if selected_choices:
                raise serializers.ValidationError(
                    {
                        "selected_choices": "Text questions should not have selected choices."
                    }
                )
        elif question.question_type == Question.QuestionType.MCQ:
            if answer_text:
                raise serializers.ValidationError(
                    {
                        "answer_text": "Multiple choice questions should not have answer text."
                    }
                )
            # Validate selected choices are from available choices
            if selected_choices:
                valid_choices = question.choices
                for choice in selected_choices:
                    if choice not in valid_choices:
                        raise serializers.ValidationError(
                            {
                                "selected_choices": f"'{choice}' is not a valid choice for this question."
                            }
                        )

        return attrs


class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for application attachments"""

    class Meta:
        model = ApplicationAttachment
        fields = ["file", "file_name", "file_type"]
        read_only_fields = ["file_size"]

    def validate_file(self, value):
        """Validate file size (max 10MB)"""
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed 10MB. Current size: {value.size / (1024 * 1024):.2f}MB"
            )
        return value


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating job applications"""

    address = ApplicantAddressSerializer(required=True)
    answers = QuestionAnswerSerializer(many=True, required=True)
    attachments = ApplicationAttachmentSerializer(many=True, required=False)

    class Meta:
        model = JobApplication
        fields = [
            "job_profile",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "answers",
            "attachments",
        ]

    def validate_job_profile(self, value):
        """Validate job profile is active"""
        if not value.is_active:
            raise serializers.ValidationError(
                "This job posting is no longer accepting applications."
            )
        return value

    def validate_answers(self, value):
        """Validate all required questions are answered"""
        if not value:
            raise serializers.ValidationError("At least one answer is required.")
        return value

    def create(self, validated_data):
        """Create job application with related models"""
        address_data = validated_data.pop("address")
        answers_data = validated_data.pop("answers")
        attachments_data = validated_data.pop("attachments", [])

        # Create job application
        job_application = JobApplication.objects.create(**validated_data)

        # Create address
        ApplicantAddress.objects.create(job_application=job_application, **address_data)

        # Create answers
        for answer_data in answers_data:
            QuestionAnswer.objects.create(
                job_application=job_application, **answer_data
            )

        # Create attachments
        for attachment_data in attachments_data:
            file = attachment_data.get("file")
            ApplicationAttachment.objects.create(
                job_application=job_application,
                file_size=file.size,
                **attachment_data,
            )

        return job_application


class JobApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing job application details"""

    address = ApplicantAddressSerializer(read_only=True)
    answers = QuestionAnswerSerializer(many=True, read_only=True)
    attachments = ApplicationAttachmentSerializer(many=True, read_only=True)
    job_profile_title = serializers.CharField(
        source="job_profile.title", read_only=True
    )

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "job_profile",
            "job_profile_title",
            "first_name",
            "last_name",
            "email",
            "phone",
            "status",
            "address",
            "answers",
            "attachments",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
