import uuid
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField


class AIScreeningConfiguration(models.Model):
    """
    Configuration for AI-powered screening of job applications.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_screening_configurations"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class JobCategory(models.Model):
    """
    Categories for job profiles (e.g., Engineering, Marketing, Sales).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_categories"
        ordering = ["title"]
        verbose_name_plural = "Job Categories"

    def __str__(self):
        return self.title


class ExperienceLevel(models.Model):
    """
    Experience levels for job profiles (e.g., Entry Level, Mid-Level, Senior).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "experience_levels"
        ordering = ["title"]

    def __str__(self):
        return self.title


class JobProfile(models.Model):
    """
    Job profile model representing job positions with requirements and screening configuration.
    """

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        FREELANCE = "freelance", "Freelance"
        NOT_APPLICABLE = "not_applicable", "Not Applicable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="job_profiles",
        help_text="Organization that owns this job profile",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_job_profiles",
        help_text="User who created this job profile",
    )
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.PROTECT,
        related_name="job_profiles",
        help_text="Job category",
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    experience_level = models.ForeignKey(
        ExperienceLevel,
        on_delete=models.PROTECT,
        related_name="job_profiles",
        help_text="Required experience level",
    )
    description = models.TextField(help_text="Detailed job description")
    requirements = ArrayField(
        models.TextField(),
        default=list,
        blank=True,
        help_text="List of job requirements",
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of skill objects with 'skill' and 'is_required' fields",
    )
    ai_screening_configuration = models.ForeignKey(
        AIScreeningConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_profiles",
        help_text="AI screening configuration for this job",
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether the job profile is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.category}) - {self.organization.name}"


class Question(models.Model):
    """
    Questions for job profiles to gather applicant information.
    """

    class QuestionType(models.TextChoices):
        TEXT = "text", "Text"
        MCQ = "mcq", "Multiple Choice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_profile = models.ForeignKey(
        JobProfile,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="Job profile this question belongs to",
    )
    text = models.TextField(help_text="Question text")
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Display order of the question"
    )
    choices = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of choice strings for multiple choice questions",
    )
    is_required = models.BooleanField(
        default=True, help_text="Whether this question must be answered"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        ordering = ["job_profile", "order"]

    def __str__(self):
        return f"{self.text[:50]} ({self.question_type}) - {self.job_profile.title}"
