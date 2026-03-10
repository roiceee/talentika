import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from organizations.models import OrganizationMembership
from job_applications.models import JobApplication

from .models import ApplicationAnalysis
from .serializers import (
    ApplicationAnalysisSerializer,
    ApplicationAnalysisStatusSerializer,
    ApplicationAnalysisListItemSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Test endpoint — extract text from uploaded PDF (no DB, no queue)
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="post",
    operation_description=(
        "**Test endpoint** — upload a PDF file and get the OCR-extracted text back "
        "immediately.  Does NOT create any database records or trigger the analysis "
        "pipeline.  Useful for verifying doctr is working."
    ),
    manual_parameters=[
        openapi.Parameter(
            "file",
            openapi.IN_FORM,
            description="PDF file to extract text from",
            type=openapi.TYPE_FILE,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            "Extracted text",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "text": openapi.Schema(type=openapi.TYPE_STRING),
                    "pages": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        400: "No file provided",
    },
    security=[],
    tags=["Analysis (Test)"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def test_resume_extraction(request):
    """Upload a PDF and get OCR text back (stateless test)."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"file": "No file was provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from .ocr_service import extract_text_from_pdf_bytes

    pdf_bytes = uploaded_file.read()
    text = extract_text_from_pdf_bytes(pdf_bytes)
    page_count = text.count("--- Page ")

    return Response({"text": text, "pages": page_count}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Get analysis result for a single application
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="get",
    operation_description=(
        "Retrieve the analysis result for a specific job application.  "
        "The requesting user must be a member of the application's organization."
    ),
    manual_parameters=[
        openapi.Parameter(
            "application_id",
            openapi.IN_PATH,
            description="Job application UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        200: ApplicationAnalysisSerializer,
        404: "Application or analysis not found",
    },
    tags=["Analysis"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_analysis(request, application_id):
    """Return the full analysis for a job application."""
    try:
        application = JobApplication.objects.select_related(
            "job_profile__organization"
        ).get(id=application_id)
    except JobApplication.DoesNotExist:
        return Response(
            {"detail": "Job application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Permission check — user must belong to the org
    org = application.job_profile.organization
    is_member = OrganizationMembership.objects.filter(
        user=request.user, organization=org
    ).exists()
    if not (is_member or request.user.is_superuser):
        return Response(
            {"detail": "You do not have permission to view this analysis."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        analysis = ApplicationAnalysis.objects.get(job_application=application)
    except ApplicationAnalysis.DoesNotExist:
        return Response(
            {"detail": "Analysis not found for this application."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ApplicationAnalysisSerializer(analysis)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Re-trigger analysis for a failed application
# ---------------------------------------------------------------------------


@swagger_auto_schema(
    method="post",
    operation_description=(
        "Re-trigger the analysis pipeline for a FAILED or UPLOADED application analysis.  "
        "UPLOADED analyses may be stuck when Redis was unavailable during submission.  "
        "Resets the status to UPLOADED and re-enqueues the OCR task."
    ),
    manual_parameters=[
        openapi.Parameter(
            "application_id",
            openapi.IN_PATH,
            description="Job application UUID",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        200: openapi.Response("Analysis re-triggered"),
        400: "Analysis is not in FAILED state",
        404: "Application or analysis not found",
    },
    tags=["Analysis"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_analysis(request, application_id):
    """Re-trigger a failed analysis."""
    try:
        application = JobApplication.objects.select_related(
            "job_profile__organization"
        ).get(id=application_id)
    except JobApplication.DoesNotExist:
        return Response(
            {"detail": "Job application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Permission check
    org = application.job_profile.organization
    is_member = OrganizationMembership.objects.filter(
        user=request.user, organization=org
    ).exists()
    if not (is_member or request.user.is_superuser):
        return Response(
            {"detail": "You do not have permission."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        analysis = ApplicationAnalysis.objects.get(job_application=application)
    except ApplicationAnalysis.DoesNotExist:
        return Response(
            {"detail": "Analysis not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    retryable_statuses = (
        ApplicationAnalysis.Status.FAILED,
        ApplicationAnalysis.Status.UPLOADED,
    )
    if analysis.status not in retryable_statuses:
        return Response(
            {
                "detail": f"Analysis is in '{analysis.status}' state, not subject for retry."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Reset and re-enqueue
    analysis.status = ApplicationAnalysis.Status.UPLOADED
    analysis.error_message = ""
    analysis.save(update_fields=["status", "error_message", "updated_at"])

    from .workers import enqueue_ocr

    enqueue_ocr(str(analysis.id))

    return Response(
        {"detail": "Analysis re-triggered.", "analysis_id": str(analysis.id)},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# List analyses for an org's job profile (with filters & sort)
# ---------------------------------------------------------------------------

_VALID_SORT_FIELDS = {
    "score": "score",
    "created_at": "created_at",
    "updated_at": "updated_at",
    "-score": "-score",
    "-created_at": "-created_at",
    "-updated_at": "-updated_at",
}

_STATUS_CHOICES = [s[0] for s in ApplicationAnalysis.Status.choices]


@swagger_auto_schema(
    method="get",
    operation_description=(
        "List all application analyses for a specific job profile within an "
        "organization, with optional filtering by pipeline status and score range, "
        "sorting by score or timestamp, and cursor-based pagination.\n\n"
        "**Filters** (all optional):\n"
        "- `status` — one of: uploaded, ocr_pending, ocr_done, ai_pending, done, failed\n"
        "- `min_score` / `max_score` — integer 0-100 (only meaningful when status=done)\n\n"
        "**Sort** (optional):\n"
        "- `sort_by` — field to sort on: `score`, `created_at`, `updated_at` (default: `created_at`)\n"
        "- `order` — `asc` or `desc` (default: `desc`)\n\n"
        "**Pagination**:\n"
        "- `page` — page number (default: 1)\n"
        "- `page_size` — results per page, max 100 (default: 20)\n"
    ),
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
            "status",
            openapi.IN_QUERY,
            description="Filter by pipeline status",
            type=openapi.TYPE_STRING,
            enum=_STATUS_CHOICES,
            required=False,
        ),
        openapi.Parameter(
            "min_score",
            openapi.IN_QUERY,
            description="Minimum AI score (0-100, inclusive)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "max_score",
            openapi.IN_QUERY,
            description="Maximum AI score (0-100, inclusive)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "sort_by",
            openapi.IN_QUERY,
            description="Field to sort by",
            type=openapi.TYPE_STRING,
            enum=["score", "created_at", "updated_at"],
            required=False,
        ),
        openapi.Parameter(
            "order",
            openapi.IN_QUERY,
            description="Sort direction",
            type=openapi.TYPE_STRING,
            enum=["asc", "desc"],
            required=False,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number (default: 1)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Results per page, max 100 (default: 20)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            "Paginated list of analyses",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Total number of results"
                    ),
                    "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "page": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Current page"
                    ),
                    "page_size": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    ),
                },
            ),
        ),
        400: "Invalid query parameter",
        403: "Not a member of the organization",
        404: "Organization or job profile not found",
    },
    tags=["Analysis"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_analyses(request, org_id, job_profile_id):
    """
    List application analyses for a specific job profile within an organization.

    Supports filtering by status, min_score, max_score, sorting by score /
    created_at / updated_at, and page-based pagination.
    """
    from organizations.models import Organization
    from job_profile.models import JobProfile

    # --- org existence + membership ---
    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    is_member = OrganizationMembership.objects.filter(
        user=request.user, organization=organization
    ).exists()
    if not (is_member or request.user.is_superuser):
        return Response(
            {
                "detail": "You do not have permission to view this organization's analyses."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # --- verify job profile belongs to the org ---
    try:
        JobProfile.objects.get(id=job_profile_id, organization=organization)
    except JobProfile.DoesNotExist:
        return Response(
            {"detail": "Job profile not found in this organization."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # --- base queryset (always scoped to the given job profile) ---
    qs = ApplicationAnalysis.objects.filter(
        job_application__job_profile__id=job_profile_id,
    ).select_related(
        "job_application",
        "job_application__job_profile",
    )

    # --- filters ---
    status_filter = request.query_params.get("status")
    if status_filter:
        if status_filter not in _STATUS_CHOICES:
            return Response(
                {
                    "detail": f"Invalid status '{status_filter}'. Choose from: {', '.join(_STATUS_CHOICES)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = qs.filter(status=status_filter)

    min_score = request.query_params.get("min_score")
    if min_score is not None:
        try:
            qs = qs.filter(score__gte=int(min_score))
        except ValueError:
            return Response(
                {"detail": "min_score must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    max_score = request.query_params.get("max_score")
    if max_score is not None:
        try:
            qs = qs.filter(score__lte=int(max_score))
        except ValueError:
            return Response(
                {"detail": "max_score must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # --- sort ---
    sort_by = request.query_params.get("sort_by", "created_at")
    order = request.query_params.get("order", "desc")

    allowed_sort_fields = ("score", "created_at", "updated_at")
    if sort_by not in allowed_sort_fields:
        return Response(
            {
                "detail": f"Invalid sort_by '{sort_by}'. Choose from: {', '.join(allowed_sort_fields)}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if order not in ("asc", "desc"):
        return Response(
            {"detail": "order must be 'asc' or 'desc'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    order_prefix = "" if order == "asc" else "-"
    qs = qs.order_by(f"{order_prefix}{sort_by}")

    # --- pagination ---
    _DEFAULT_PAGE_SIZE = 20
    _MAX_PAGE_SIZE = 100

    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except ValueError:
        return Response(
            {"detail": "page must be an integer."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        page_size = min(
            _MAX_PAGE_SIZE,
            max(1, int(request.query_params.get("page_size", _DEFAULT_PAGE_SIZE))),
        )
    except ValueError:
        return Response(
            {"detail": "page_size must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    total_count = qs.count()
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    page_qs = qs[offset : offset + page_size]

    serializer = ApplicationAnalysisListItemSerializer(page_qs, many=True)
    return Response(
        {
            "count": total_count,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )
