from rest_framework import serializers
from users.models import User
from organizations.models import OrganizationMembership, OrganizationInvitation


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User registration"""

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    invitation_token = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "invitation_token",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        """Validate password confirmation and optional invitation token"""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        # Validate invitation token if provided
        invitation_token = attrs.get("invitation_token")
        if invitation_token:
            try:
                invitation = OrganizationInvitation.objects.get(token=invitation_token)

                # Check if invitation is valid
                if invitation.accepted_at:
                    raise serializers.ValidationError(
                        {
                            "invitation_token": "This invitation has already been accepted."
                        }
                    )

                if invitation.is_expired():
                    raise serializers.ValidationError(
                        {"invitation_token": "This invitation has expired."}
                    )

                # Check if email matches
                if attrs.get("email").lower() != invitation.email.lower():
                    raise serializers.ValidationError(
                        {
                            "invitation_token": f"This invitation is for {invitation.email}, but you registered with {attrs.get('email')}."
                        }
                    )

                # Store invitation in context for create method
                attrs["_invitation"] = invitation
            except OrganizationInvitation.DoesNotExist:
                raise serializers.ValidationError(
                    {"invitation_token": "Invalid invitation token."}
                )

        return attrs

    def create(self, validated_data):
        """Create user with hashed password and handle invitation"""
        validated_data.pop("password_confirm")
        invitation_token = validated_data.pop("invitation_token", None)
        invitation = validated_data.pop("_invitation", None)

        # Create user
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        # If invitation exists, create membership and mark as accepted
        if invitation:
            OrganizationMembership.objects.create(
                user=user,
                organization=invitation.organization,
                role=invitation.role,
            )
            invitation.accept()
            # Auto-select the invited org as the user's default
            user.default_organization = invitation.organization
            user.save(update_fields=["default_organization"])

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (excluding email)"""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "default_organization"]
        read_only_fields = ["id"]

    def validate_default_organization(self, value):
        """Ensure user is a member of the default organization"""
        if value is not None:
            from organizations.models import OrganizationMembership

            user = self.instance
            if not OrganizationMembership.objects.filter(
                user=user, organization=value
            ).exists():
                raise serializers.ValidationError(
                    "You must be a member of this organization to set it as default."
                )
        return value

    def validate_username(self, value):
        """Ensure username is unique if changed"""
        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing user profile"""

    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "default_organization",
            "profile_picture_url",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None
        from job_applications.storage import get_storage

        try:
            return get_storage().get_url(obj.profile_picture)
        except Exception:
            return None


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer without sensitive fields"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
