import uuid
from django.db import models


class ApplicationAnalysis(models.Model):
    """
    Tracks the OCR + AI analysis pipeline for a single job application.

    Status flow: UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE / FAILED
    """

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        OCR_PENDING = "ocr_pending", "OCR Pending"
        OCR_DONE = "ocr_done", "OCR Done"
        AI_PENDING = "ai_pending", "AI Pending"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_application = models.OneToOneField(
        "job_applications.JobApplication",
        on_delete=models.CASCADE,
        related_name="analysis",
        help_text="The job application being analysed",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error details when status is FAILED",
    )

    # --- OCR output ---
    extracted_resume_text = models.TextField(
        blank=True,
        help_text="Full text extracted from the resume PDF via doctr",
    )

    # --- AI output (structured) ---
    ai_analysis_summary = models.TextField(
        blank=True,
        help_text="High-level summary from AI",
    )
    notable_traits = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of notable trait strings",
    )
    key_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of key skill strings",
    )
    score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="AI-assigned score 0-100",
    )
    detailed_analysis = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Structured object: strengths, areas_for_development, "
            "experience[], education[], certifications[]"
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application_analyses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis({self.status}) – {self.job_application}"
