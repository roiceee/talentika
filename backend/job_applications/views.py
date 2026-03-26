import os

from django.db.models import F, IntegerField, OuterRef, Q, Subquery
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

    allowed_extensions = {".pdf", ".doc", ".docx"}
    allowed_content_types = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if (
        file_ext not in allowed_extensions
        and uploaded_file.content_type not in allowed_content_types
    ):
        return Response(
            {"file": "Only PDF, DOC, and DOCX files are allowed."},
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
    List job applications for a specific job profile (paginated, filterable, sortable).

    Supports server-side pagination, search by name/email, status filter,
    and ordering by any listed column.
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
            "page",
            openapi.IN_QUERY,
            description="Page number (1-based, default 1)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Results per page (default 10, max 100)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "search",
            openapi.IN_QUERY,
            description="Search by first name, last name, or email",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "status",
            openapi.IN_QUERY,
            description="Filter by application status (to_be_reviewed, reviewed, shortlisted, rejected)",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "ordering",
            openapi.IN_QUERY,
            description="Sort field. Prefix with '-' for descending. Options: submitted_at, first_name, last_name, status, score",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            "Paginated list of job applications",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "page": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "page_size": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "num_pages": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    ),
                },
            ),
        ),
        403: "Forbidden - user is not a member of the organization",
        404: "Organization or job profile not found",
    },
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def list_job_applications(request, org_id, job_profile_id):
    """
    Return paginated, filterable, sortable job applications for the given job profile.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    from job_application_analysis.models import ApplicationAnalysis

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

    # Annotate with the related analysis score for ordering
    score_subquery = Subquery(
        ApplicationAnalysis.objects.filter(job_application=OuterRef("pk")).values(
            "score"
        )[:1],
        output_field=IntegerField(),
    )

    qs = (
        JobApplication.objects.filter(job_profile=job_profile)
        .select_related("job_profile", "address")
        .prefetch_related("answers", "attachments", "analysis")
        .annotate(analysis_score=score_subquery)
    )

    # Search
    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    # Status filter
    status_filter = request.query_params.get("status", "").strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Skill filter — supports multiple values (OR logic)
    skill_filters = [s.strip() for s in request.query_params.getlist("skill") if s.strip()]
    if skill_filters:
        skill_q = Q()
        for skill in skill_filters:
            skill_q |= Q(analysis__key_skills__contains=[skill])
        qs = qs.filter(skill_q)

    # Trait filter — supports multiple values (OR logic)
    trait_filters = [t.strip() for t in request.query_params.getlist("trait") if t.strip()]
    if trait_filters:
        trait_q = Q()
        for trait in trait_filters:
            trait_q |= Q(analysis__notable_traits__contains=[trait])
        qs = qs.filter(trait_q)

    # Ordering
    VALID_ORDERINGS = {
        "submitted_at": "submitted_at",
        "-submitted_at": "-submitted_at",
        "first_name": "first_name",
        "-first_name": "-first_name",
        "last_name": "last_name",
        "-last_name": "-last_name",
        "status": "status",
        "-status": "-status",
    }
    ordering_param = request.query_params.get("ordering", "-submitted_at")
    if ordering_param == "score":
        qs = qs.order_by(F("analysis_score").asc(nulls_last=True))
    elif ordering_param == "-score":
        qs = qs.order_by(F("analysis_score").desc(nulls_last=True))
    else:
        db_ordering = VALID_ORDERINGS.get(ordering_param, "-submitted_at")
        qs = qs.order_by(db_ordering)

    # Pagination
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(100, max(1, int(request.query_params.get("page_size", 10))))
    except (ValueError, TypeError):
        page_size = 10

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    serializer = JobApplicationDetailWithAnalysisSerializer(
        list(page_obj.object_list), many=True
    )
    return Response(
        {
            "count": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "num_pages": paginator.num_pages,
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


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
    - shortlisted → reviewed, rejected
    - rejected → reviewed, shortlisted

    Once an application has moved away from ``to_be_reviewed`` it cannot be
    reverted back to that status.
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

    # Once an application has left 'to_be_reviewed' it cannot be reverted.
    if (
        new_status == JobApplication.Status.TO_BE_REVIEWED
        and job_application.status != JobApplication.Status.TO_BE_REVIEWED
    ):
        return Response(
            {"detail": "Cannot revert status back to 'to_be_reviewed' once it has been reviewed."},
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

    # Category distribution (matches score_categories.py thresholds)
    category_distribution = {
        "suitable": analyses.filter(score__gte=70).count(),
        "potentially_suitable": analyses.filter(score__gte=40, score__lte=69).count(),
        "unsuitable": analyses.filter(score__gte=0, score__lte=39).count(),
    }

    avg_score = analyses.aggregate(avg=Avg("score"))["avg"]

    # Average score category
    from job_application_analysis.score_categories import get_score_category

    avg_score_rounded = round(avg_score, 1) if avg_score is not None else None
    avg_cat = get_score_category(avg_score_rounded)
    average_category = {"key": avg_cat.key, "label": avg_cat.label} if avg_cat else None

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
            "category_distribution": category_distribution,
            "average_category": average_category,
            "top_skills": top_skills,
            "top_traits": top_traits,
            "applications_over_time": applications_over_time,
        },
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="get",
    operation_description="""
    Get org-wide analytics aggregated across all job profiles in the organization.

    Returns:
    - **total_applications**: Total across all job profiles
    - **total_job_profiles**: Dict with total, active, inactive counts
    - **status_breakdown**: Count per application status
    - **category_distribution**: AI score category counts (suitable/potentially_suitable/unsuitable)
    - **average_category**: Org-wide average score category
    - **top_skills**: Most frequent skills across all analyses (top 15)
    - **top_traits**: Most frequent traits across all analyses (top 10)
    - **applications_over_time**: Daily application counts (last 30 days)
    - **applications_by_job_profile**: Per-profile breakdown with title, count, avg_score_category
    - **employment_type_breakdown**: Application counts by job profile employment type
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
    ],
    responses={200: "Org analytics object"},
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def org_analytics(request, org_id):
    """Return aggregate analytics across all job profiles in an organization."""
    from collections import Counter
    from datetime import timedelta
    from django.db.models import Avg, Count
    from django.utils import timezone

    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    job_profiles = JobProfile.objects.filter(organization=organization)
    total_profiles = job_profiles.count()
    active_profiles = job_profiles.filter(is_active=True).count()

    applications = JobApplication.objects.filter(job_profile__organization=organization)
    total = applications.count()

    # --- Status breakdown ---
    status_breakdown = dict(
        applications.values_list("status")
        .annotate(count=Count("id"))
        .values_list("status", "count")
    )

    # --- AI analysis stats ---
    from job_application_analysis.models import ApplicationAnalysis
    from job_application_analysis.score_categories import get_score_category

    analyses = ApplicationAnalysis.objects.filter(
        job_application__job_profile__organization=organization,
        status=ApplicationAnalysis.Status.DONE,
    )

    category_distribution = {
        "suitable": analyses.filter(score__gte=70).count(),
        "potentially_suitable": analyses.filter(score__gte=40, score__lte=69).count(),
        "unsuitable": analyses.filter(score__gte=0, score__lte=39).count(),
    }

    avg_score = analyses.aggregate(avg=Avg("score"))["avg"]
    avg_score_rounded = round(avg_score, 1) if avg_score is not None else None
    avg_cat = get_score_category(avg_score_rounded)
    average_category = {"key": avg_cat.key, "label": avg_cat.label} if avg_cat else None

    # Top skills & traits
    skill_counter = Counter()
    trait_counter = Counter()
    for skills, traits in analyses.values_list("key_skills", "notable_traits"):
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

    # --- Per-job-profile breakdown ---
    profile_rows = (
        job_profiles.annotate(app_count=Count("applications"))
        .values("id", "title", "employment_type", "is_active", "app_count")
        .order_by("-app_count")
    )
    applications_by_job_profile = []
    for row in profile_rows:
        profile_analyses = analyses.filter(job_application__job_profile_id=row["id"])
        profile_avg = profile_analyses.aggregate(avg=Avg("score"))["avg"]
        profile_avg_rounded = round(profile_avg, 1) if profile_avg is not None else None
        profile_cat = get_score_category(profile_avg_rounded)
        applications_by_job_profile.append(
            {
                "id": str(row["id"]),
                "title": row["title"],
                "employment_type": row["employment_type"],
                "is_active": row["is_active"],
                "application_count": row["app_count"],
                "avg_score_category": (
                    {"key": profile_cat.key, "label": profile_cat.label}
                    if profile_cat
                    else None
                ),
            }
        )

    # --- Employment type breakdown ---
    employment_type_breakdown = dict(
        applications.values("job_profile__employment_type")
        .annotate(count=Count("id"))
        .values_list("job_profile__employment_type", "count")
    )

    return Response(
        {
            "total_applications": total,
            "total_job_profiles": {
                "total": total_profiles,
                "active": active_profiles,
                "inactive": total_profiles - active_profiles,
            },
            "status_breakdown": status_breakdown,
            "category_distribution": category_distribution,
            "average_category": average_category,
            "top_skills": top_skills,
            "top_traits": top_traits,
            "applications_over_time": applications_over_time,
            "applications_by_job_profile": applications_by_job_profile,
            "employment_type_breakdown": employment_type_breakdown,
        },
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Application results summary (grouped by status)
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="get",
    operation_description=(
        "Get a summary of job applications grouped by status. "
        "Returns counts and a preview of applications per status category."
    ),
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
    ],
    responses={200: "Results summary", 403: "Forbidden"},
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def application_results_summary(request, org_id, job_profile_id):
    """Return application counts and preview rows for each status category."""
    from django.db.models import Count

    job_profile = JobProfile.objects.filter(
        id=job_profile_id, organization_id=org_id
    ).first()
    if not job_profile:
        return Response(
            {"error": "Job profile not found."}, status=status.HTTP_404_NOT_FOUND
        )

    applications = JobApplication.objects.filter(job_profile=job_profile)

    # Counts per status
    status_counts = dict(
        applications.values("status")
        .annotate(count=Count("id"))
        .values_list("status", "count")
    )

    # For each status, get top 5 with analysis
    categories = []
    for status_choice, status_label in JobApplication.Status.choices:
        count = status_counts.get(status_choice, 0)
        preview_apps = applications.filter(status=status_choice).order_by(
            "-submitted_at"
        )[:5]
        preview = JobApplicationDetailWithAnalysisSerializer(
            preview_apps, many=True
        ).data
        categories.append(
            {
                "status": status_choice,
                "label": status_label,
                "count": count,
                "preview": preview,
            }
        )

    return Response({"categories": categories}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Export: request, poll, download
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="post",
    operation_description=(
        "Request an async export of job applications (with analysis) as CSV or XLSX. "
        "The export is processed via RQ and can be polled for status."
    ),
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "application_status": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Filter by application status (blank for all)",
                enum=["", "to_be_reviewed", "reviewed", "shortlisted", "rejected"],
            ),
            "format": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Export format",
                enum=["csv", "xlsx"],
                default="xlsx",
            ),
        },
    ),
    responses={201: "Export job created", 403: "Forbidden"},
    tags=["Job Applications"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def request_export(request, org_id, job_profile_id):
    """Create an export job and enqueue it on RQ."""
    from .models import ApplicationExportJob
    from .export_worker import enqueue_export

    job_profile = JobProfile.objects.filter(
        id=job_profile_id, organization_id=org_id
    ).first()
    if not job_profile:
        return Response(
            {"error": "Job profile not found."}, status=status.HTTP_404_NOT_FOUND
        )

    app_status = request.data.get("application_status", "")
    export_format = request.data.get("format", "xlsx")
    if export_format not in ("csv", "xlsx"):
        export_format = "xlsx"

    export_job = ApplicationExportJob.objects.create(
        job_profile=job_profile,
        requested_by=request.user,
        application_status=app_status,
        export_format=export_format,
    )

    try:
        enqueue_export(str(export_job.id))
    except Exception as exc:
        logger.exception("Failed to enqueue export job %s", export_job.id)
        export_job.status = ApplicationExportJob.ExportStatus.FAILED
        export_job.error_message = str(exc)
        export_job.save(update_fields=["status", "error_message"])
        return Response(
            {"error": "Failed to start export. Is Redis running?"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {
            "id": str(export_job.id),
            "status": export_job.status,
            "format": export_job.export_format,
            "application_status": export_job.application_status,
        },
        status=status.HTTP_201_CREATED,
    )


@swagger_auto_schema(
    method="get",
    operation_description="Poll the status of an export job.",
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "export_id",
            openapi.IN_PATH,
            description="Export job UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
    ],
    responses={200: "Export job status"},
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def poll_export(request, org_id, job_profile_id, export_id):
    """Return the current status of an export job."""
    from .models import ApplicationExportJob

    export_job = ApplicationExportJob.objects.filter(
        id=export_id,
        job_profile_id=job_profile_id,
        job_profile__organization_id=org_id,
    ).first()
    if not export_job:
        return Response(
            {"error": "Export job not found."}, status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            "id": str(export_job.id),
            "status": export_job.status,
            "format": export_job.export_format,
            "application_status": export_job.application_status,
            "error_message": (
                export_job.error_message if export_job.status == "failed" else ""
            ),
        }
    )


@swagger_auto_schema(
    method="get",
    operation_description="Download a completed export file.",
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "job_profile_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
        openapi.Parameter(
            "export_id",
            openapi.IN_PATH,
            description="Export job UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
        ),
    ],
    responses={200: "File download", 404: "Not found"},
    tags=["Job Applications"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def download_export(request, org_id, job_profile_id, export_id):
    """Serve the completed export file."""
    from django.http import FileResponse
    from pathlib import Path
    from .models import ApplicationExportJob

    export_job = ApplicationExportJob.objects.filter(
        id=export_id,
        job_profile_id=job_profile_id,
        job_profile__organization_id=org_id,
    ).first()
    if not export_job:
        return Response(
            {"error": "Export job not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if export_job.status != ApplicationExportJob.ExportStatus.DONE:
        return Response(
            {"error": "Export not ready."}, status=status.HTTP_400_BAD_REQUEST
        )

    file_path = Path(export_job.file_path)
    if not file_path.exists():
        return Response(
            {"error": "Export file not found."}, status=status.HTTP_404_NOT_FOUND
        )

    content_type = (
        "text/csv"
        if export_job.export_format == "csv"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return FileResponse(
        open(file_path, "rb"),
        content_type=content_type,
        as_attachment=True,
        filename=file_path.name,
    )
