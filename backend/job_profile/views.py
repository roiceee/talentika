from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from organizations.models import Organization
from organizations.models.organization_membership import OrganizationMembership
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

    is_member = (
        request.user.is_superuser
        or OrganizationMembership.objects.filter(
            user=request.user, organization=organization
        ).exists()
    )
    if not is_member:
        return Response(
            {"error": "You must be a member of this organization to create job profiles."},
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
    operation_description="Update a job profile. Any organization member can update a job profile.",
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

    is_member = (
        request.user.is_superuser
        or OrganizationMembership.objects.filter(
            user=request.user, organization=job_profile.organization
        ).exists()
    )
    if not is_member:
        return Response(
            {"error": "You must be a member of this organization to update job profiles."},
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


@swagger_auto_schema(
    method="delete",
    operation_description="Soft-delete a job profile. Only organization admins or the creator can delete.",
    responses={
        204: "Job profile deleted successfully",
        403: "Forbidden",
        404: "Job profile not found",
    },
    tags=["Job Profiles"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_job_profile(request, job_id):
    """
    Soft-delete a job profile.

    Sets deleted_at so the job profile is hidden from all queries.
    Only organization admins can perform this action.
    """
    job_profile = get_object_or_404(
        JobProfile.objects.select_related("organization"), id=job_id
    )

    is_admin = request.user.is_superuser or OrganizationMembership.objects.filter(
        user=request.user,
        organization=job_profile.organization,
        role="ORG_ADMIN",
    ).exists()
    if not is_admin:
        return Response(
            {"error": "Only organization admins can delete job profiles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    job_profile.deleted_at = timezone.now()
    job_profile.save(update_fields=["deleted_at"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method="delete",
    operation_description="Soft-delete a job profile within an organization. Verifies the job profile belongs to the org and that the requester is an admin of that org.",
    responses={
        204: "Job profile deleted successfully",
        403: "Forbidden — not an org admin",
        404: "Job profile or organization not found",
    },
    tags=["Job Profiles"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_org_job_profile(request, org_id, job_id):
    """
    Soft-delete a job profile scoped to an organization.

    Ensures:
    - The organization exists.
    - The job profile belongs to that organization.
    - The requesting user is an ORG_ADMIN of that organization.
    """
    organization = get_object_or_404(Organization, id=org_id)
    job_profile = get_object_or_404(
        JobProfile.objects.select_related("organization"),
        id=job_id,
        organization=organization,
    )

    is_admin = request.user.is_superuser or OrganizationMembership.objects.filter(
        user=request.user,
        organization=organization,
        role="ORG_ADMIN",
    ).exists()
    if not is_admin:
        return Response(
            {"error": "Only organization admins can delete job profiles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    job_profile.deleted_at = timezone.now()
    job_profile.save(update_fields=["deleted_at"])
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Org-specific job categories ─────────────────────────────────────────────

@swagger_auto_schema(method='get', tags=['Job Profile - Reference Data'], responses={200: 'list'})
@swagger_auto_schema(method='post', tags=['Job Profile - Reference Data'], responses={201: 'created', 400: 'error', 403: 'forbidden'})
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_create_org_job_categories(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not OrganizationMembership.objects.filter(organization=org, user=request.user).exists():
        return Response({"detail": "Not a member."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        from django.db.models import Q as DQ
        qs = JobCategory.objects.filter(DQ(organization=None) | DQ(organization=org)).order_by('title')
        data = [{"id": str(c.id), "title": c.title, "is_custom": c.organization_id is not None} for c in qs]
        return Response(data)

    # POST — only admins
    membership = OrganizationMembership.objects.filter(organization=org, user=request.user).first()
    if not membership or membership.role != "ORG_ADMIN":
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

    title = (request.data.get("title") or "").strip()
    if not title:
        return Response({"title": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    if JobCategory.objects.filter(organization=org, title=title).exists():
        return Response({"title": ["A category with this title already exists."]}, status=status.HTTP_400_BAD_REQUEST)

    cat = JobCategory.objects.create(organization=org, title=title)
    return Response({"id": str(cat.id), "title": cat.title, "is_custom": True}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='delete', tags=['Job Profile - Reference Data'], responses={204: 'deleted', 403: 'forbidden', 404: 'not found'})
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_org_job_category(request, org_id, category_id):
    org = get_object_or_404(Organization, id=org_id)
    membership = OrganizationMembership.objects.filter(organization=org, user=request.user).first()
    if not membership or membership.role != "ORG_ADMIN":
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

    cat = get_object_or_404(JobCategory, id=category_id, organization=org)
    if cat.job_profiles.exists():
        return Response({"detail": "Cannot delete: category is in use by job profiles."}, status=status.HTTP_400_BAD_REQUEST)
    cat.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Org-specific experience levels ──────────────────────────────────────────

@swagger_auto_schema(method='get', tags=['Job Profile - Reference Data'], responses={200: 'list'})
@swagger_auto_schema(method='post', tags=['Job Profile - Reference Data'], responses={201: 'created', 400: 'error', 403: 'forbidden'})
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_create_org_experience_levels(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not OrganizationMembership.objects.filter(organization=org, user=request.user).exists():
        return Response({"detail": "Not a member."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        from django.db.models import Q as DQ
        qs = ExperienceLevel.objects.filter(DQ(organization=None) | DQ(organization=org)).order_by('title')
        data = [{"id": str(l.id), "title": l.title, "is_custom": l.organization_id is not None} for l in qs]
        return Response(data)

    membership = OrganizationMembership.objects.filter(organization=org, user=request.user).first()
    if not membership or membership.role != "ORG_ADMIN":
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

    title = (request.data.get("title") or "").strip()
    if not title:
        return Response({"title": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    if ExperienceLevel.objects.filter(organization=org, title=title).exists():
        return Response({"title": ["An experience level with this title already exists."]}, status=status.HTTP_400_BAD_REQUEST)

    level = ExperienceLevel.objects.create(organization=org, title=title)
    return Response({"id": str(level.id), "title": level.title, "is_custom": True}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='delete', tags=['Job Profile - Reference Data'], responses={204: 'deleted', 403: 'forbidden', 404: 'not found'})
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_org_experience_level(request, org_id, level_id):
    org = get_object_or_404(Organization, id=org_id)
    membership = OrganizationMembership.objects.filter(organization=org, user=request.user).first()
    if not membership or membership.role != "ORG_ADMIN":
        return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

    level = get_object_or_404(ExperienceLevel, id=level_id, organization=org)
    if level.job_profiles.exists():
        return Response({"detail": "Cannot delete: level is in use by job profiles."}, status=status.HTTP_400_BAD_REQUEST)
    level.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
