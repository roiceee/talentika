from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that uses email instead of username for authentication.
    """

    username_field = User.EMAIL_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field if it exists and add email field
        if "username" in self.fields:
            del self.fields["username"]
        if self.username_field not in self.fields:
            self.fields[self.username_field] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["name"] = user.get_full_name()
        token["is_superuser"] = user.is_superuser

        return token


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    Takes email and password and returns access and refresh tokens.
    Use the access token in the Authorization header as: Bearer <access_token>
    """

    serializer_class = EmailTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="""Login with email and password to obtain JWT tokens.
        
        Returns:
        - access: JWT access token (valid for 1 hour)
        - refresh: JWT refresh token (valid for 7 days)
        
        Use the access token in the Authorization header:
        Authorization: Bearer <access_token>
        
        When the access token expires, use the refresh token to get a new access token via /api/auth/refresh/
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User's email address",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="User's password",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT access token (expires in 1 hour)",
                        ),
                        "refresh": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT refresh token (expires in 7 days)",
                        ),
                    },
                ),
            ),
            401: "Invalid credentials",
        },
        security=[],  # No authentication required for login
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
