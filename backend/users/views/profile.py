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
