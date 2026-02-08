import uuid
from django.db import models
from django.core.validators import EmailValidator


class JobApplication(models.Model):
    """
    Job application submitted by anonymous applicants.
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_profile = models.ForeignKey(
        "job_profile.JobProfile",
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="Job profile this application is for",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_applications"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["job_profile", "status"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job_profile.title}"


class ApplicantAddress(models.Model):
    """
    Address information for job applicant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="address",
        help_text="Job application this address belongs to",
    )
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    province_state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(
        max_length=2, help_text="ISO 3166-1 alpha-2 country code"
    )

    class Meta:
        db_table = "applicant_addresses"

    def __str__(self):
        return f"{self.city}, {self.country} - {self.job_application}"


class QuestionAnswer(models.Model):
    """
    Answer to a question submitted by applicant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text="Job application this answer belongs to",
    )
    question = models.ForeignKey(
        "job_profile.Question",
        on_delete=models.PROTECT,
        related_name="answers",
        help_text="Question being answered",
    )
    answer_text = models.TextField(
        blank=True,
        null=True,
        help_text="Answer text for text-type questions",
    )
    selected_choices = models.JSONField(
        default=list,
        blank=True,
        help_text="Selected choices for MCQ questions (array of strings)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_answers"
        unique_together = [["job_application", "question"]]
        indexes = [
            models.Index(fields=["job_application"]),
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"Answer to '{self.question.text[:30]}' by {self.job_application}"


class ApplicationAttachment(models.Model):
    """
    File attachments for job application (resume, cover letter, etc.).
    """

    class FileType(models.TextChoices):
        RESUME = "resume", "Resume"
        COVER_LETTER = "cover_letter", "Cover Letter"
        PORTFOLIO = "portfolio", "Portfolio"
        CERTIFICATE = "certificate", "Certificate"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="attachments",
        help_text="Job application this attachment belongs to",
    )
    file = models.FileField(
        upload_to="job_applications/%Y/%m/%d/",
        help_text="Uploaded file",
    )
    file_name = models.CharField(max_length=255, help_text="Original filename")
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_attachments"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["job_application", "file_type"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.file_type}) - {self.job_application}"
