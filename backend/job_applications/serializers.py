from rest_framework import serializers
from .models import (
    JobApplication,
    ApplicantAddress,
    QuestionAnswer,
    ApplicationAttachment,
    TemporaryFileUpload,
)
from job_profile.models import Question
from django.core.files.uploadedfile import InMemoryUploadedFile
from .storage import get_storage
from .duplicate_detection import find_duplicates, DUPLICATE_THRESHOLD


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
    """Serializer for question answers (write path — create only)"""

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

        is_mcq = question.question_type in (
            Question.QuestionType.MCQ,
            Question.QuestionType.MCQ_SINGLE,
        )

        # Check if required question is answered
        if question.is_required:
            if question.question_type == Question.QuestionType.TEXT and not answer_text:
                raise serializers.ValidationError(
                    {"answer_text": f"Answer is required for question: {question.text}"}
                )
            if is_mcq and not selected_choices:
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
        elif is_mcq:
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
            # Single-select: only one choice allowed
            if (
                question.question_type == Question.QuestionType.MCQ_SINGLE
                and len(selected_choices) > 1
            ):
                raise serializers.ValidationError(
                    {
                        "selected_choices": "This question only allows one selected choice."
                    }
                )

        return attrs


class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for application attachments"""

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationAttachment
        fields = ["file_url", "file_name", "file_type", "file_size", "uploaded_at"]
        read_only_fields = ["file_url", "file_size", "uploaded_at"]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        try:
            return get_storage().get_url(obj.file)
        except Exception:
            return None


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating job applications"""

    address = ApplicantAddressSerializer(required=True)
    answers = QuestionAnswerSerializer(many=True, required=False)
    resume_id = serializers.UUIDField(
        required=False,
        write_only=True,
        help_text="File ID returned by the resume upload endpoint (POST /api/applications/submit/upload/resume/)",
    )

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
            "resume_id",
        ]

    def validate_email(self, value):
        """Validate that email has not already been used to apply for this job profile"""
        job_profile = self.initial_data.get("job_profile")
        if (
            job_profile
            and JobApplication.objects.filter(
                job_profile_id=job_profile, email=value
            ).exists()
        ):
            raise serializers.ValidationError(
                "You have already applied for this job with this email address."
            )
        return value

    def validate_job_profile(self, value):
        """Validate job profile is active"""
        if not value.is_active:
            raise serializers.ValidationError(
                "This job posting is no longer accepting applications."
            )
        return value

    def _check_duplicates(self, attrs):
        """Run duplicate detection and raise if a duplicate is found."""
        job_profile = attrs.get("job_profile")
        resume_id = attrs.get("resume_id")
        sha256_hash = None
        if resume_id:
            try:
                temp = TemporaryFileUpload.objects.get(id=resume_id)
                sha256_hash = temp.sha256_hash or None
            except TemporaryFileUpload.DoesNotExist:
                pass

        duplicates = find_duplicates(
            job_profile=job_profile,
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            phone=attrs.get("phone", ""),
            sha256_hash=sha256_hash,
            threshold=DUPLICATE_THRESHOLD,
        )
        if duplicates:
            top = duplicates[0]
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        f"A similar application already exists "
                        f"(duplicate score: {top.duplicate_score:.0%}). "
                        "Duplicate submissions are not allowed."
                    )
                }
            )

    def validate(self, attrs):
        """Validate answers based on job profile questions"""
        job_profile = attrs.get("job_profile")
        answers = attrs.get("answers", [])

        # Get all questions for this job profile
        questions = job_profile.questions.all()

        # If job profile has no questions, answers should be empty
        if not questions.exists():
            if answers:
                raise serializers.ValidationError(
                    {"answers": "This job posting does not have any questions."}
                )
            self._check_duplicates(attrs)
            return attrs

        # If job profile has questions, validate all required questions are answered
        answered_question_ids = {answer["question"].id for answer in answers}
        required_questions = questions.filter(is_required=True)

        missing_questions = []
        for question in required_questions:
            if question.id not in answered_question_ids:
                missing_questions.append(question.text)

        if missing_questions:
            raise serializers.ValidationError(
                {
                    "answers": f"Missing required answers for questions: {', '.join(missing_questions[:3])}{'...' if len(missing_questions) > 3 else ''}"
                }
            )

        # Validate that all answered questions belong to this job profile
        valid_question_ids = {q.id for q in questions}
        for answer in answers:
            if answer["question"].id not in valid_question_ids:
                raise serializers.ValidationError(
                    {
                        "answers": f"Question '{answer['question'].text}' does not belong to this job profile."
                    }
                )

        self._check_duplicates(attrs)
        return attrs

    def validate_resume_id(self, value):
        """Validate that the resume_id references an existing temporary upload."""
        try:
            TemporaryFileUpload.objects.get(id=value)
        except TemporaryFileUpload.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid resume_id: no uploaded file found with this ID."
            )
        return value

    def create(self, validated_data):
        """Create job application with related models"""
        address_data = validated_data.pop("address")
        answers_data = validated_data.pop("answers", [])
        resume_id = validated_data.pop("resume_id", None)

        # if resume_id is not present, throw error since resume is required
        if not resume_id:
            raise serializers.ValidationError(
                {
                    "resume_id": "Resume file is required. Please upload your resume and provide the resume_id."
                }
            )

        # Create job application
        job_application = JobApplication.objects.create(**validated_data)

        # Create address
        ApplicantAddress.objects.create(job_application=job_application, **address_data)

        # Create answers
        for answer_data in answers_data:
            QuestionAnswer.objects.create(
                job_application=job_application, **answer_data
            )

        # Attach the pre-uploaded resume if a resume_id was supplied
        if resume_id:
            try:
                temp_upload = TemporaryFileUpload.objects.get(id=resume_id)
                ApplicationAttachment.objects.create(
                    job_application=job_application,
                    file=temp_upload.storage_path,
                    file_name=temp_upload.file_name,
                    file_type=ApplicationAttachment.FileType.RESUME,
                    file_size=temp_upload.file_size,
                    sha256_hash=temp_upload.sha256_hash or "",
                )
                # Clean up the temporary record
                temp_upload.delete()
            except TemporaryFileUpload.DoesNotExist:
                pass  # Already validated; silently skip if race condition

        return job_application


class JobApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing job application details"""

    address = ApplicantAddressSerializer(read_only=True)
    answers = serializers.SerializerMethodField()
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

    def get_answers(self, obj):
        """Return answers with their related question details."""
        answers = obj.answers.select_related("question").all()
        return [
            {
                "question_id": str(a.question_id),
                "question_text": a.question.text,
                "question_type": a.question.question_type,
                "choices": a.question.choices,
                "is_required": a.question.is_required,
                "answer_text": a.answer_text,
                "selected_choices": a.selected_choices,
            }
            for a in answers
        ]


class JobApplicationDetailWithAnalysisSerializer(JobApplicationDetailSerializer):
    """Serializer for viewing job application details with related analysis"""

    analysis = serializers.SerializerMethodField()

    class Meta(JobApplicationDetailSerializer.Meta):
        fields = JobApplicationDetailSerializer.Meta.fields + ["analysis"]

    def get_analysis(self, obj):
        from job_application_analysis.models import ApplicationAnalysis
        from job_application_analysis.serializers import (
            BaseApplicationAnalysisSerializer,
        )

        try:
            return BaseApplicationAnalysisSerializer(obj.analysis).data
        except ApplicationAnalysis.DoesNotExist:
            return None
