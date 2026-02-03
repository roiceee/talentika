from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import User, Organization, OrganizationMembership


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

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
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )
        return user


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer without sensitive fields"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership"""

    user = UserBasicSerializer(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user",
            "organization",
            "organization_name",
            "role",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization with membership details"""

    memberships = OrganizationMembershipSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(source="memberships.count", read_only=True)
    can_invite = serializers.BooleanField(source="can_invite_users", read_only=True)
    approved_by_email = serializers.EmailField(
        source="approved_by.email", read_only=True
    )

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "address",
            "status",
            "created_at",
            "approved_at",
            "approved_by_email",
            "memberships",
            "member_count",
            "can_invite",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "approved_at",
            "approved_by_email",
        ]

    def validate_name(self, value):
        """Validate organization name uniqueness"""
        if Organization.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "An organization with this name already exists."
            )
        return value


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new organization"""

    class Meta:
        model = Organization
        fields = ["name", "address"]

    def validate_name(self, value):
        """Validate organization name uniqueness"""
        if Organization.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                "An organization with this name already exists."
            )
        return value


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing organizations"""

    member_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "status", "created_at", "member_count"]


class OrganizationApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting organizations"""

    action = serializers.ChoiceField(choices=["approve", "reject", "suspend"])

    def validate_action(self, value):
        """Validate that action is valid for current organization status"""
        organization = self.context.get("organization")
        if not organization:
            raise serializers.ValidationError("Organization context is required.")

        if value == "approve" and organization.status != Organization.Status.PENDING:
            raise serializers.ValidationError(
                "Only pending organizations can be approved."
            )

        if value == "reject" and organization.status != Organization.Status.PENDING:
            raise serializers.ValidationError(
                "Only pending organizations can be rejected."
            )

        if value == "suspend" and organization.status != Organization.Status.APPROVED:
            raise serializers.ValidationError(
                "Only approved organizations can be suspended."
            )

        return value
