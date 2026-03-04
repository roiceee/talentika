import uuid
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField


class JobCategory(models.Model):
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


class Qualification(models.Model):
    """
    Unified qualification requirement for a job profile.
    Replaces the old separate requirements (ArrayField) and skills (JSONField).
    """

    class Category(models.TextChoices):
        SKILL = "skill", "Skill"
        EXPERIENCE = "experience", "Experience"
        EDUCATION = "education", "Education"
        CERTIFICATION = "certification", "Certification"
        TOOL = "tool", "Tool"
        LANGUAGE = "language", "Language"
        OTHER = "other", "Other"

    class RequirementLevel(models.TextChoices):
        REQUIRED = "required", "Required"
        PREFERRED = "preferred", "Preferred"

    class ProficiencyLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_profile = models.ForeignKey(
        JobProfile,
        on_delete=models.CASCADE,
        related_name="qualifications",
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    name = models.CharField(max_length=255)
    requirement_level = models.CharField(
        max_length=10,
        choices=RequirementLevel.choices,
        default=RequirementLevel.REQUIRED,
    )
    years_required = models.PositiveIntegerField(null=True, blank=True)
    proficiency_level = models.CharField(
        max_length=15,
        choices=ProficiencyLevel.choices,
        null=True,
        blank=True,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "qualifications"
        ordering = ["category", "order", "name"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name} ({self.get_requirement_level_display()})"


class Question(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = "text", "Text"
        MCQ = "mcq", "Multiple Choice (Multi-Select)"
        MCQ_SINGLE = "mcq_single", "Multiple Choice (Single Select)"

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
    choices = ArrayField(
        models.TextField(),
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
