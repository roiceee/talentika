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
from .models import JobApplication, TemporaryFileUpload
from .serializers import JobApplicationCreateSerializer, JobApplicationDetailSerializer
from .storage import get_storage


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
        .prefetch_related("answers", "attachments")
    )

    serializer = JobApplicationDetailSerializer(applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
