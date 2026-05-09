import logging

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from organizations.permissions import IsOrganizationAdmin
from organizations.models import Organization
from organizations.serializers import OrganizationSerializer
from job_applications.storage import get_storage

logger = logging.getLogger(__name__)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@swagger_auto_schema(
    method="post",
    operation_description="""
    Upload or replace an organization's profile picture.
    Only organization admins can perform this action.

    Accepts multipart/form-data with a single `file` field.
    Allowed types: JPEG, PNG, WebP. Max size: 5 MB.
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
            "file",
            openapi.IN_FORM,
            description="Profile picture file (JPEG, PNG, or WebP)",
            type=openapi.TYPE_FILE,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            "Organization with updated picture", OrganizationSerializer
        ),
        400: "Invalid file",
        403: "Not an admin",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrganizationAdmin])
@parser_classes([MultiPartParser])
def upload_org_profile_picture(request, org_id):
    """Upload or replace the organization's profile picture."""
    file = request.FILES.get("file")
    if not file:
        return Response(
            {"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
        )

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return Response(
            {
                "detail": f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WebP."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.size > MAX_FILE_SIZE:
        return Response(
            {"detail": "File too large. Maximum size is 5 MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    storage = get_storage()

    # Delete old picture if exists
    if org.profile_picture:
        try:
            storage.delete(org.profile_picture)
        except Exception:
            pass

    ext = file.name.rsplit(".", 1)[-1] if "." in file.name else "jpg"
    import uuid as _uuid

    storage_path = (
        f"profile_pictures/organizations/{org.id}/{_uuid.uuid4().hex[:12]}.{ext}"
    )
    try:
        storage_path, _url = storage.save_at_path(
            file=file,
            storage_path=storage_path,
            content_type=file.content_type,
        )
    except Exception:
        logger.exception("Failed to upload org profile picture for org %s", org_id)
        return Response(
            {"detail": "Failed to upload file. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    org.profile_picture = storage_path
    org.save(update_fields=["profile_picture"])

    serializer = OrganizationSerializer(org)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="delete",
    operation_description="Remove the organization's profile picture. Only admins.",
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
    responses={
        200: openapi.Response(
            "Organization with picture removed", OrganizationSerializer
        ),
        403: "Not an admin",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsOrganizationAdmin])
def delete_org_profile_picture(request, org_id):
    """Remove the organization's profile picture."""
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"detail": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if org.profile_picture:
        storage = get_storage()
        try:
            storage.delete(org.profile_picture)
        except Exception:
            pass
        org.profile_picture = None
        org.save(update_fields=["profile_picture"])

    serializer = OrganizationSerializer(org)
    return Response(serializer.data, status=status.HTTP_200_OK)
