import logging

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..serializers import UserProfileSerializer
from job_applications.storage import get_storage

logger = logging.getLogger(__name__)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@swagger_auto_schema(
    method="post",
    operation_description="""
    Upload or replace the authenticated user's profile picture.

    Accepts multipart/form-data with a single `file` field.
    Allowed types: JPEG, PNG, WebP. Max size: 5 MB.
    The image should already be cropped to 1:1 by the client.
    """,
    manual_parameters=[
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
            "Profile with updated picture URL", UserProfileSerializer
        ),
        400: "Invalid file",
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_profile_picture(request):
    """Upload or replace the user's profile picture."""
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

    storage = get_storage()
    user = request.user

    # Delete old picture if exists
    if user.profile_picture:
        try:
            storage.delete(user.profile_picture)
        except Exception:
            pass

    # Save new picture under profile_pictures/users/<user_id>/
    ext = file.name.rsplit(".", 1)[-1] if "." in file.name else "jpg"
    import uuid as _uuid

    storage_path = f"profile_pictures/users/{user.id}/{_uuid.uuid4().hex[:12]}.{ext}"
    try:
        storage_path, _url = storage.save_at_path(
            file=file,
            storage_path=storage_path,
            content_type=file.content_type,
        )
    except Exception:
        logger.exception("Failed to upload profile picture for user %s", user.id)
        return Response(
            {"detail": "Failed to upload file. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    user.profile_picture = storage_path
    user.save(update_fields=["profile_picture"])

    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="delete",
    operation_description="Remove the authenticated user's profile picture.",
    responses={
        200: openapi.Response("Profile with picture removed", UserProfileSerializer),
    },
    tags=["Users"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_profile_picture(request):
    """Remove the user's profile picture."""
    user = request.user
    if user.profile_picture:
        storage = get_storage()
        try:
            storage.delete(user.profile_picture)
        except Exception:
            pass
        user.profile_picture = None
        user.save(update_fields=["profile_picture"])

    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
