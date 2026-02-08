from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from organizations.models import Organization, is_org_admin
from .models import (
    AIScreeningConfiguration,
    JobCategory,
    ExperienceLevel,
    JobProfile,
)
from .serializers import (
    AIScreeningConfigurationSerializer,
    JobCategorySerializer,
    ExperienceLevelSerializer,
    JobProfileListSerializer,
    JobProfileDetailSerializer,
    JobProfileCreateSerializer,
)


# Supporting Models Endpoints


@swagger_auto_schema(
    method="get",
    operation_description="Get all job categories. Used for populating category dropdown when creating job profiles.",
    responses={200: JobCategorySerializer(many=True)},
    tags=["Job Profile - Reference Data"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_job_categories(request):
    """Get all available job categories"""
    categories = JobCategory.objects.all()
    serializer = JobCategorySerializer(categories, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    operation_description="Get all experience levels. Used for populating experience level dropdown when creating job profiles.",
    responses={200: ExperienceLevelSerializer(many=True)},
    tags=["Job Profile - Reference Data"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_experience_levels(request):
    """Get all available experience levels"""
    levels = ExperienceLevel.objects.all()
    serializer = ExperienceLevelSerializer(levels, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    operation_description="Get all AI screening configurations. Used for populating AI screening dropdown when creating job profiles.",
    responses={200: AIScreeningConfigurationSerializer(many=True)},
    tags=["Job Profile - Reference Data"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_ai_screening_configs(request):
    """Get all available AI screening configurations"""
    configs = AIScreeningConfiguration.objects.all()
    serializer = AIScreeningConfigurationSerializer(configs, many=True)
    return Response(serializer.data)


# Job Profile Endpoints


@swagger_auto_schema(
    method="post",
    operation_description="""
    Create a new job profile for an organization.
    
    Only organization admins can create job profiles for their organization.
    The authenticated user will be set as the creator.
    """,
    request_body=JobProfileCreateSerializer,
    responses={
        201: JobProfileDetailSerializer,
        400: "Validation error",
        403: "User is not an admin of the organization",
    },
    tags=["Job Profiles"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job_profile(request):
    """
    Create a new job profile.
    User must be an admin of the specified organization.
    """
    # Extract organization from request data for validation
    organization_id = request.data.get("organization")
    if not organization_id:
        return Response(
            {"organization": ["This field is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response(
            {"organization": ["Invalid organization ID."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user is org admin
    if not is_org_admin(request.user, organization):
        return Response(
            {
                "error": "Only organization admins can create job profiles for their organization."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Pass organization through context, not validated_data
    serializer = JobProfileCreateSerializer(
        data=request.data, context={"organization": organization}
    )

    if serializer.is_valid():
        # Create job profile with authenticated user as creator
        job_profile = serializer.save(created_by=request.user)

        # Return detailed response
        response_serializer = JobProfileDetailSerializer(job_profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    operation_description="""
    Get all job profiles for a specific organization.
    
    Returns a list of job profiles with preview information.
    User must be a member of the organization to view its job profiles.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
        )
    ],
    responses={
        200: JobProfileListSerializer(many=True),
        403: "User is not a member of this organization",
        404: "Organization not found",
    },
    tags=["Job Profiles"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_organization_job_profiles(request, org_id):
    """
    Get all job profiles for an organization.
    User must be a member of the organization.
    """
    organization = get_object_or_404(Organization, id=org_id)

    # Check if user is a member (or superuser)
    if not request.user.is_superuser:
        if not organization.memberships.filter(user=request.user).exists():
            return Response(
                {"error": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

    # Get all job profiles for this organization
    job_profiles = JobProfile.objects.filter(organization=organization).select_related(
        "category", "experience_level", "organization", "created_by"
    )

    serializer = JobProfileListSerializer(job_profiles, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    operation_description="""
    Get detailed information about a specific job profile (PUBLIC endpoint).
    
    Returns complete job profile information including description, requirements, skills, questions, and AI screening configuration.
    No authentication required - this is a public endpoint for job seekers.
    """,
    manual_parameters=[
        openapi.Parameter(
            "job_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
        )
    ],
    responses={
        200: JobProfileDetailSerializer,
        404: "Job profile not found",
    },
    security=[],  # No authentication required
    tags=["Job Profiles"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_job_profile(request, job_id):
    """
    Get detailed information about a specific job profile.
    Public endpoint - no authentication required.
    """
    job_profile = get_object_or_404(
        JobProfile.objects.select_related(
            "category",
            "experience_level",
            "organization",
            "created_by",
            "ai_screening_configuration",
        ).prefetch_related("questions"),
        id=job_id,
    )

    serializer = JobProfileDetailSerializer(job_profile)
    return Response(serializer.data)


@swagger_auto_schema(
    method="patch",
    operation_description="""
    Update an existing job profile.
    
    Only organization admins can update job profiles for their organization.
    Partial updates are supported - only include fields you want to change.
    """,
    manual_parameters=[
        openapi.Parameter(
            "job_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
        )
    ],
    request_body=JobProfileCreateSerializer,
    responses={
        200: JobProfileDetailSerializer,
        400: "Validation error",
        403: "User is not an admin of the organization",
        404: "Job profile not found",
    },
    tags=["Job Profiles"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_job_profile(request, job_id):
    """
    Update an existing job profile.
    User must be an admin of the organization that owns the job profile.
    """
    # Reject if organization field is in request body
    if "organization" in request.data:
        return Response(
            {"organization": ["Organization cannot be changed after creation."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    job_profile = get_object_or_404(
        JobProfile.objects.select_related("organization"), id=job_id
    )

    # Check if user is org admin
    if not is_org_admin(request.user, job_profile.organization):
        return Response(
            {
                "error": "Only organization admins can update job profiles for their organization."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = JobProfileCreateSerializer(
        job_profile, data=request.data, partial=True
    )

    if serializer.is_valid():
        serializer.save()

        # Return detailed response
        job_profile.refresh_from_db()
        response_serializer = JobProfileDetailSerializer(job_profile)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
