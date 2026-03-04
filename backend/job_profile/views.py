from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from organizations.models import Organization, is_org_admin
from .models import (
    JobCategory,
    ExperienceLevel,
    JobProfile,
)
from .serializers import (
    JobCategorySerializer,
    ExperienceLevelSerializer,
    JobProfileListSerializer,
    JobProfileDetailSerializer,
    JobProfileCreateSerializer,
)


@swagger_auto_schema(
    method="get",
    operation_description="Get all job categories.",
    responses={200: JobCategorySerializer(many=True)},
    tags=["Job Profile - Reference Data"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_job_categories(request):
    categories = JobCategory.objects.all()
    serializer = JobCategorySerializer(categories, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    operation_description="Get all experience levels.",
    responses={200: ExperienceLevelSerializer(many=True)},
    tags=["Job Profile - Reference Data"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_experience_levels(request):
    levels = ExperienceLevel.objects.all()
    serializer = ExperienceLevelSerializer(levels, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    operation_description="Create a new job profile for an organization.",
    request_body=JobProfileCreateSerializer,
    responses={
        201: JobProfileDetailSerializer,
        400: "Validation error",
        403: "Forbidden",
    },
    tags=["Job Profiles"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job_profile(request):
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

    if not is_org_admin(request.user, organization):
        return Response(
            {"error": "Only organization admins can create job profiles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = JobProfileCreateSerializer(
        data=request.data, context={"organization": organization}
    )

    if serializer.is_valid():
        job_profile = serializer.save(created_by=request.user)
        response_serializer = JobProfileDetailSerializer(job_profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    operation_description="List job profiles for an organization.",
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="Organization UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
        )
    ],
    responses={200: JobProfileListSerializer(many=True)},
    tags=["Job Profiles"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_organization_job_profiles(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)

    if not request.user.is_superuser:
        if not organization.memberships.filter(user=request.user).exists():
            return Response(
                {"error": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

    job_profiles = JobProfile.objects.filter(organization=organization).select_related(
        "category", "experience_level", "organization", "created_by"
    )

    serializer = JobProfileListSerializer(job_profiles, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    operation_description="Get a specific job profile (PUBLIC).",
    manual_parameters=[
        openapi.Parameter(
            "job_id",
            openapi.IN_PATH,
            description="Job Profile UUID",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
        )
    ],
    responses={200: JobProfileDetailSerializer},
    security=[],
    tags=["Job Profiles"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_job_profile(request, job_id):
    job_profile = get_object_or_404(
        JobProfile.objects.select_related(
            "category",
            "experience_level",
            "organization",
            "created_by",
        ).prefetch_related("questions", "qualifications"),
        id=job_id,
    )

    serializer = JobProfileDetailSerializer(job_profile)
    return Response(serializer.data)


@swagger_auto_schema(
    method="patch",
    operation_description="Update a job profile.",
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
        403: "Forbidden",
    },
    tags=["Job Profiles"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_job_profile(request, job_id):
    if "organization" in request.data:
        return Response(
            {"organization": ["Organization cannot be changed after creation."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    job_profile = get_object_or_404(
        JobProfile.objects.select_related("organization"), id=job_id
    )

    if not is_org_admin(request.user, job_profile.organization):
        return Response(
            {"error": "Only organization admins can update job profiles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # When there are submissions, only is_active may be changed.
    has_applications = job_profile.applications.exists()
    if has_applications:
        disallowed = {k for k in request.data if k != "is_active"}
        if disallowed:
            return Response(
                {
                    "error": "This job profile has submissions and can only have its active status changed."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = JobProfileCreateSerializer(
        job_profile, data=request.data, partial=True
    )

    if serializer.is_valid():
        serializer.save()
        job_profile.refresh_from_db()
        response_serializer = JobProfileDetailSerializer(job_profile)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
