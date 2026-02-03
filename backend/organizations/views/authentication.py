from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..serializers import UserSerializer


@swagger_auto_schema(
    method="post",
    operation_description="""
    Register a new user account.
    
    Optional: Include an invitation_token to automatically join an organization.
    - If invitation_token is provided and valid, user will be added to the organization upon registration
    - Email must match the email the invitation was sent to
    - Invitation must not be expired or already accepted
    """,
    request_body=UserSerializer,
    responses={
        201: openapi.Response("User created successfully", UserSerializer),
        400: "Validation error or invalid invitation token",
    },
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user account.

    Users can register with or without an invitation:
    - Without invitation: Creates a standalone user account
    - With invitation: Creates account and automatically joins the organization

    The invitation_token parameter is optional and can be obtained from invitation emails.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
