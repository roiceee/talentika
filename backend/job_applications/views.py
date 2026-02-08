from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    JobApplicationCreateSerializer,
    JobApplicationDetailSerializer,
)
from .models import JobApplication


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
        detail_serializer = JobApplicationDetailSerializer(job_application)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
