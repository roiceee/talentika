from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from job_profile.models import JobProfile
from organizations.models import Organization
from organizations.permissions import IsOrganizationMember
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .emails import send_application_confirmation_email
from .duplicate_detection import compute_sha256
from .models import JobApplication, ApplicationAttachment, TemporaryFileUpload
from .serializers import (
    JobApplicationCreateSerializer,
    JobApplicationDetailSerializer,
    JobApplicationDetailWithAnalysisSerializer,
)
from .storage import get_storage

import logging

logger = logging.getLogger(__name__)


def _trigger_analysis_pipeline(job_application):
    """Create an ApplicationAnalysis row and enqueue OCR processing.

    Fails silently so that the submission response is never blocked by
    analysis infrastructure issues (Redis down, etc.).
    """
    try:
        from job_application_analysis.models import ApplicationAnalysis
        from job_application_analysis.workers import enqueue_ocr

        # Only trigger if application has a resume attachment
        has_resume = job_application.attachments.filter(file_type="resume").exists()
        if not has_resume:
            logger.info(
                "Skipping analysis for application %s — no resume attached.",
                job_application.id,
            )
            return

        analysis, created = ApplicationAnalysis.objects.get_or_create(
            job_application=job_application,
        )
        if created:
            enqueue_ocr(str(analysis.id))
            logger.info(
                "Analysis pipeline triggered for application %s",
                job_application.id,
            )
    except Exception:
        logger.exception(
            "Failed to trigger analysis pipeline for application %s",
            job_application.id,
        )


@swagger_auto_schema(
    method="post",
    operation_description="""
    Submit a job application (PUBLIC endpoint - no authentication required).
    
    Required fields:
    - job_profile: UUID of the job profile
    - first_name, last_name, email, phone: Applicant contact information
    - address: Complete address object
    - answers: Array of answers to job questions (must answer all required questions)
    
    Optional:
    - attachments: Array of file attachments (resume, cover letter, etc.)
    
    Note: 
    - All required questions must be answered
    - File size limit: 10MB per file
    - Job profile must be active to accept applications
    """,
    request_body=JobApplicationCreateSerializer,
    responses={
        201: openapi.Response(
            "Application submitted successfully", JobApplicationDetailSerializer
        ),
        400: "Validation error - missing required fields or invalid data",
    },
    security=[],  # No authentication required
    tags=["Job Applications"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def submit_job_application(request):
    """
    Submit a job application for a specific job profile.
    Public endpoint - no authentication required.
    """
    serializer = JobApplicationCreateSerializer(data=request.data)

    if serializer.is_valid():
        job_application = serializer.save()
        send_application_confirmation_email(job_application)

        # Kick off the OCR → AI analysis pipeline
        _trigger_analysis_pipeline(job_application)

        detail_serializer = JobApplicationDetailSerializer(job_application)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Upload a resume file to temporary storage before submitting a job application.

    - Accepts a single file via multipart form data (field name: ``file``).
    - The file is uploaded to S3 and a temporary record is created.
    - Returns a ``file_id`` (UUID) that must be supplied as ``resume_id`` when
      calling ``POST /api/applications/submit/``.
    - The temporary record is automatically deleted after a successful application
      submission.

    Allowed file types: PDF, DOC, DOCX (enforced client-side; server validates size).
    File size limit: 10 MB.
    """,
    manual_parameters=[
        openapi.Parameter(
            "file",
            openapi.IN_FORM,
            description="Resume file to upload",
            type=openapi.TYPE_FILE,
            required=True,
        )
    ],
    responses={
        201: openapi.Response(
            "File uploaded successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "file_id": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format="uuid",
                        description="Temporary file ID to pass as resume_id on submission",
                    ),
                    "file_name": openapi.Schema(type=openapi.TYPE_STRING),
                    "file_size": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="File size in bytes",
                    ),
                },
            ),
        ),
        400: "Validation error - no file provided or file too large",
    },
    security=[],
    tags=["Job Applications"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def upload_resume(request):
    """
    Upload a resume to temporary storage and return a file_id for use during
    application submission.
    """
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"file": "No file was provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    max_size = 10 * 1024 * 1024  # 10 MB
    if uploaded_file.size > max_size:
        return Response(
            {
                "file": (
                    f"File size cannot exceed 10 MB. "
                    f"Current size: {uploaded_file.size / (1024 * 1024):.2f} MB"
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    storage = get_storage()
    sha256_hash = compute_sha256(uploaded_file)
    storage_path, _ = storage.save(
        file=uploaded_file,
        filename=uploaded_file.name,
        content_type=uploaded_file.content_type or "application/octet-stream",
        metadata={"purpose": "resume"},
    )

    temp_upload = TemporaryFileUpload.objects.create(
        storage_path=storage_path,
        file_name=uploaded_file.name,
        file_size=uploaded_file.size,
        content_type=uploaded_file.content_type or "",
        sha256_hash=sha256_hash,
    )

    return Response(
        {
            "file_id": str(temp_upload.id),
            "file_name": temp_upload.file_name,
            "file_size": temp_upload.file_size,
        },
        status=status.HTTP_201_CREATED,
    )


@swagger_auto_schema(
    method="get",
    operation_description="""
    List job applications for a specific organization (authenticated members only).

    - Returns all applications that belong to the organization's job profiles.
    - Optionally filter by a specific job profile using ``?job_profile_id=<uuid>``.
    - The requesting user must be a member of the organization.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_QUERY,
            description="Filter by job profile UUID (must belong to the organization)",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=False,
        ),
    ],
    responses={
        200: JobApplicationDetailSerializer(many=True),
        403: "Forbidden - user is not a member of the organization",
        404: "Organization or job profile not found",
    },
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def list_job_applications(request, org_id, job_profile_id):
    """
    Return all job applications for the given organization and job profile.
    """
    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_profile = JobProfile.objects.get(
            id=job_profile_id, organization=organization
        )
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )
    applications = (
        JobApplication.objects.filter(job_profile=job_profile)
        .select_related("job_profile", "address")
        .prefetch_related("answers", "attachments", "analysis")
    )

    serializer = JobApplicationDetailWithAnalysisSerializer(applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_description="""
    Retrieve a specific job application for an organization and job profile.

    - The requesting user must be a member of the organization.
    - The job profile must belong to the organization.
    - The job application must belong to the job profile.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job profile UUID (must belong to the organization)",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_application_id",
            openapi.IN_PATH,
            description="Job application UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        200: JobApplicationDetailWithAnalysisSerializer(),
        403: "Forbidden - user is not a member of the organization",
        404: "Organization, job profile, or job application not found",
    },
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def get_job_application(request, org_id, job_profile_id, job_application_id):
    """
    Return a specific job application for the given organization and job profile.
    """
    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_profile = JobProfile.objects.get(
            id=job_profile_id, organization=organization
        )
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )
    try:
        job_application = JobApplication.objects.get(
            id=job_application_id, job_profile=job_profile
        )
    except JobApplication.DoesNotExist:
        return Response(
            {"detail": "Job application not found in this job profile."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = JobApplicationDetailWithAnalysisSerializer(job_application)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Resume download
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="get",
    operation_description="""
    Download the resume attachment for a specific job application.

    Returns the raw file bytes with appropriate Content-Type and
    Content-Disposition headers so the browser triggers a download.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job profile UUID (must belong to the organization)",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_application_id",
            openapi.IN_PATH,
            description="Job application UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        200: "File download",
        404: "Resume not found",
    },
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def download_resume(request, org_id, job_profile_id, job_application_id):
    """Stream the resume file for the given application."""
    from django.http import HttpResponse

    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_profile = JobProfile.objects.get(
            id=job_profile_id, organization=organization
        )
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_application = JobApplication.objects.get(
            id=job_application_id, job_profile=job_profile
        )
    except JobApplication.DoesNotExist:
        return Response(
            {"detail": "Job application not found in this job profile."},
            status=status.HTTP_404_NOT_FOUND,
        )

    attachment = ApplicationAttachment.objects.filter(
        job_application=job_application,
        file_type=ApplicationAttachment.FileType.RESUME,
    ).first()

    if attachment is None:
        return Response(
            {"detail": "No resume found for this application."},
            status=status.HTTP_404_NOT_FOUND,
        )

    storage = get_storage()
    try:
        file_bytes = storage.get_file_bytes(attachment.file)
    except Exception:
        logger.exception(
            "Failed to download resume for application %s", job_application_id
        )
        return Response(
            {"detail": "Failed to retrieve the resume file."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Guess content type from extension
    import mimetypes

    content_type, _ = mimetypes.guess_type(attachment.file_name)
    content_type = content_type or "application/octet-stream"

    response = HttpResponse(file_bytes, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{attachment.file_name}"'
    return response


# ---------------------------------------------------------------------------
# Shortlist / update application status
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="patch",
    operation_description="""
    Update the status of a job application.

    Allowed status transitions:
    - to_be_reviewed → reviewed, shortlisted, rejected
    - reviewed → shortlisted, rejected
    - shortlisted → rejected
    - rejected → reviewed, shortlisted
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_application_id",
            openapi.IN_PATH,
            description="Job application UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["status"],
        properties={
            "status": openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=["to_be_reviewed", "reviewed", "shortlisted", "rejected"],
            ),
        },
    ),
    responses={
        200: JobApplicationDetailSerializer(),
        400: "Invalid status transition",
        404: "Not found",
    },
    tags=["Job Applications"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def update_application_status(request, org_id, job_profile_id, job_application_id):
    """Update the status of a job application (shortlist, reject, etc.)."""
    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_profile = JobProfile.objects.get(
            id=job_profile_id, organization=organization
        )
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_application = JobApplication.objects.get(
            id=job_application_id, job_profile=job_profile
        )
    except JobApplication.DoesNotExist:
        return Response(
            {"detail": "Job application not found in this job profile."},
            status=status.HTTP_404_NOT_FOUND,
        )

    new_status = request.data.get("status")
    valid_statuses = {c[0] for c in JobApplication.Status.choices}

    if new_status not in valid_statuses:
        return Response(
            {
                "detail": f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    job_application.status = new_status
    job_application.save(update_fields=["status", "updated_at"])

    serializer = JobApplicationDetailSerializer(job_application)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Analytics per job profile
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="get",
    operation_description="""
    Get analytics / statistics for a specific job profile.

    Returns:
    - **total_applications**: Total number of applications
    - **status_breakdown**: Count per application status
    - **score_distribution**: Histogram of AI match scores in buckets
      (0-20, 21-40, 41-60, 61-80, 81-100)
    - **average_score**: Mean AI score across analysed applications
    - **top_skills**: Most frequently identified skills (top 15)
    - **top_traits**: Most frequently identified notable traits (top 10)
    - **applications_over_time**: Daily application counts (last 30 days)
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={200: "Analytics object"},
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def job_profile_analytics(request, org_id, job_profile_id):
    """Return aggregate analytics for a job profile."""
    from collections import Counter
    from datetime import timedelta
    from django.db.models import Avg, Count, Q
    from django.utils import timezone

    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        job_profile = JobProfile.objects.get(
            id=job_profile_id, organization=organization
        )
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )

    applications = JobApplication.objects.filter(job_profile=job_profile)
    total = applications.count()

    # --- Status breakdown ---
    status_breakdown = dict(
        applications.values_list("status")
        .annotate(count=Count("id"))
        .values_list("status", "count")
    )

    # --- AI analysis stats ---
    from job_application_analysis.models import ApplicationAnalysis

    analyses = ApplicationAnalysis.objects.filter(
        job_application__job_profile=job_profile,
        status=ApplicationAnalysis.Status.DONE,
    )

    # Score distribution buckets
    score_distribution = {
        "0-20": analyses.filter(score__gte=0, score__lte=20).count(),
        "21-40": analyses.filter(score__gte=21, score__lte=40).count(),
        "41-60": analyses.filter(score__gte=41, score__lte=60).count(),
        "61-80": analyses.filter(score__gte=61, score__lte=80).count(),
        "81-100": analyses.filter(score__gte=81, score__lte=100).count(),
    }

    avg_score = analyses.aggregate(avg=Avg("score"))["avg"]

    # Top skills & traits
    skill_counter = Counter()
    trait_counter = Counter()
    for a in analyses.values_list("key_skills", "notable_traits"):
        skills, traits = a
        if skills:
            skill_counter.update(skills)
        if traits:
            trait_counter.update(traits)

    top_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counter.most_common(15)
    ]
    top_traits = [
        {"trait": trait, "count": count}
        for trait, count in trait_counter.most_common(10)
    ]

    # --- Applications over time (last 30 days) ---
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_counts = (
        applications.filter(submitted_at__gte=thirty_days_ago)
        .extra(select={"day": "DATE(submitted_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    applications_over_time = [
        {"date": str(row["day"]), "count": row["count"]} for row in daily_counts
    ]

    return Response(
        {
            "total_applications": total,
            "status_breakdown": status_breakdown,
            "score_distribution": score_distribution,
            "average_score": round(avg_score, 1) if avg_score is not None else None,
            "top_skills": top_skills,
            "top_traits": top_traits,
            "applications_over_time": applications_over_time,
        },
        status=status.HTTP_200_OK,
    )
