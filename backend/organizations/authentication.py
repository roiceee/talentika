from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
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
    """

    serializer_class = EmailTokenObtainPairSerializer
