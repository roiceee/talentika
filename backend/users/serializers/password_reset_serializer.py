from rest_framework import serializers
from users.models import User, PasswordResetToken


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset via email"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate that user exists with this email"""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """Validate token and password confirmation"""
        # Validate password confirmation
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )

        # Validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=attrs["token"])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid reset token."})

        if not reset_token.is_valid():
            if reset_token.used_at:
                raise serializers.ValidationError(
                    {"token": "This reset token has already been used."}
                )
            elif reset_token.is_expired():
                raise serializers.ValidationError(
                    {"token": "This reset token has expired."}
                )
            else:
                raise serializers.ValidationError({"token": "Invalid reset token."})

        attrs["reset_token"] = reset_token
        return attrs

    def save(self):
        """Set new password for user and mark token as used"""
        reset_token = self.validated_data["reset_token"]
        user = reset_token.user
        user.set_password(self.validated_data["new_password"])
        user.save()
        reset_token.mark_as_used()
        return user
