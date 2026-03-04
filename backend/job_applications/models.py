import uuid
from django.db import models
from django.core.validators import EmailValidator


class JobApplication(models.Model):
    """
    Job application submitted by anonymous applicants.
    """

    class Status(models.TextChoices):
        TO_BE_REVIEWED = "to_be_reviewed", "To Be Reviewed"
        REVIEWED = "reviewed", "Reviewed"
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
        default=Status.TO_BE_REVIEWED,
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
    file = models.CharField(
        max_length=500,
        help_text="Storage path / S3 key of the uploaded file",
    )
    file_name = models.CharField(max_length=255, help_text="Original filename")
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    sha256_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 hex digest of the file contents for deduplication",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_attachments"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["job_application", "file_type"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.file_type}) - {self.job_application}"


class TemporaryFileUpload(models.Model):
    """
    Temporarily stores an uploaded file (e.g. resume) in S3 before a job
    application is fully submitted.  The consumer receives the UUID ``id``
    as a ``file_id`` and passes it back when submitting the application.
    Records can be cleaned up after a configurable TTL.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storage_path = models.CharField(
        max_length=500,
        help_text="Path / key in the storage backend (S3 key or local path)",
    )
    file_name = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    content_type = models.CharField(
        max_length=100, blank=True, help_text="MIME type of the file"
    )
    sha256_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 hex digest computed at upload time",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "temporary_file_uploads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name} ({self.id})"


class ApplicationExportJob(models.Model):
    """
    Tracks an async export job that generates CSV or XLSX files
    containing job application data (with analysis) for a given status.
    """

    class ExportFormat(models.TextChoices):
        CSV = "csv", "CSV"
        XLSX = "xlsx", "XLSX"

    class ExportStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_profile = models.ForeignKey(
        "job_profile.JobProfile",
        on_delete=models.CASCADE,
        related_name="export_jobs",
        help_text="Job profile whose applications are being exported",
    )
    requested_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="export_jobs",
    )
    application_status = models.CharField(
        max_length=20,
        choices=JobApplication.Status.choices,
        blank=True,
        help_text="Filter applications to this status. Blank = all statuses.",
    )
    export_format = models.CharField(
        max_length=10,
        choices=ExportFormat.choices,
        default=ExportFormat.XLSX,
    )
    status = models.CharField(
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Storage path of the generated file",
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application_export_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Export({self.status}) – {self.job_profile} [{self.application_status or 'all'}]"
