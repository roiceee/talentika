from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..serializers import UserProfileSerializer, UserUpdateSerializer


@swagger_auto_schema(
    method="get",
    operation_description="Get the authenticated user's profile information",
    responses={
        200: openapi.Response("User profile", UserProfileSerializer),
        401: "Not authenticated",
    },
    tags=["Users"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get the current user's profile information.

    Returns the authenticated user's details including email, username, and names.
    Email field is read-only and cannot be changed.
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="patch",
    operation_description="""
    Update the authenticated user's profile information.
    
    Users can update:
    - username
    - first_name
    - last_name
    
    Email cannot be changed through this endpoint.
    """,
    request_body=UserUpdateSerializer,
    responses={
        200: openapi.Response("Profile updated successfully", UserProfileSerializer),
        400: "Validation error",
        401: "Not authenticated",
    },
    tags=["Users"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update the current user's profile information.

    Allows partial updates of user profile fields.
    Email cannot be changed through this endpoint for security reasons.
    """
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        # Return full profile with read-only fields
        response_serializer = UserProfileSerializer(request.user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="patch",
    operation_description="""
    Set the authenticated user's default organization.
    
    The user must be a member of the specified organization.
    Pass null to clear the default organization.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["default_organization"],
        properties={
            "default_organization": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="uuid",
                description="Organization UUID to set as default, or null to clear",
                x_nullable=True,
            ),
        },
    ),
    responses={
        200: openapi.Response("Default organization updated", UserProfileSerializer),
        400: "Validation error (e.g., not a member of the organization)",
        401: "Not authenticated",
    },
    tags=["Users"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def set_default_organization(request):
    """
    Set or clear the user's default organization.

    The user must be a member of the target organization.
    """
    serializer = UserUpdateSerializer(
        request.user,
        data={"default_organization": request.data.get("default_organization")},
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        response_serializer = UserProfileSerializer(request.user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="delete",
    operation_description="Permanently delete the authenticated user's account (soft delete). This action is irreversible.",
    responses={
        204: "Account deleted successfully",
        401: "Not authenticated",
    },
    tags=["Users"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Soft-delete the current user's account.

    Sets deleted_at and deactivates is_active so the user can no longer log in.
    """
    user = request.user
    user.soft_delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
