from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import (
    User,
    Address,
    Organization,
    OrganizationMembership,
    OrganizationInvitation,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

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

        return user


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer without sensitive fields"""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""

    class Meta:
        model = Address
        fields = [
            # "id",
            "line1",
            "line2",
            "city",
            "province_state",
            "postal_code",
            "country",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_country(self, value):
        """Validate country code is 2 characters (ISO 3166-1 alpha-2)"""
        if len(value) != 2:
            raise serializers.ValidationError(
                "Country code must be 2 characters (ISO 3166-1 alpha-2)."
            )
        return value.upper()


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership"""

    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user",
            "role",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization with membership details"""

    address = AddressSerializer(read_only=True)
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
    """Serializer for creating a new organization with optional address"""

    address = AddressSerializer(required=False, allow_null=True)

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

    def create(self, validated_data):
        """Create organization with optional address"""
        address_data = validated_data.pop("address", None)

        # Create address if provided
        address = None
        if address_data:
            address = Address.objects.create(**address_data)

        # Create organization
        organization = Organization.objects.create(address=address, **validated_data)
        return organization

    def update(self, instance, validated_data):
        """Update organization and optionally create/update address"""
        address_data = validated_data.pop("address", None)

        # Handle address update/creation
        if address_data:
            if instance.address:
                # Update existing address
                for key, value in address_data.items():
                    setattr(instance.address, key, value)
                instance.address.save()
            else:
                # Create new address
                address = Address.objects.create(**address_data)
                instance.address = address

        # Update organization fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing organizations"""

    address = AddressSerializer(read_only=True)
    member_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "address", "status", "created_at", "member_count"]


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


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationInvitation"""

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    invited_by_email = serializers.EmailField(source="invited_by.email", read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "organization",
            "organization_name",
            "email",
            "role",
            "invited_by_email",
            "accepted_at",
            "expires_at",
            "created_at",
            "is_valid",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "token",
            "invited_by",
            "accepted_at",
            "expires_at",
            "created_at",
        ]


class InvitationCreateSerializer(serializers.Serializer):
    """Serializer for creating invitations"""

    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=OrganizationInvitation.Role.choices,
        default=OrganizationInvitation.Role.MEMBER,
    )

    def validate_email(self, value):
        """Validate email format and check for existing invitations"""
        value = value.lower().strip()

        # Check if user is already a member of this specific organization
        organization = self.context.get("organization")
        if organization:
            try:
                user = User.objects.get(email=value)
                if OrganizationMembership.objects.filter(
                    user=user, organization=organization
                ).exists():
                    raise serializers.ValidationError(
                        "User with this email is already a member of this organization."
                    )
            except User.DoesNotExist:
                pass  # User doesn't exist yet, that's fine

            # Check for pending invitations to this organization
            pending_invite = OrganizationInvitation.objects.filter(
                organization=organization, email=value, accepted_at__isnull=True
            ).first()
            if pending_invite and pending_invite.is_valid():
                raise serializers.ValidationError(
                    "A valid invitation already exists for this email."
                )

        return value


class InvitationValidateSerializer(serializers.Serializer):
    """Serializer for validating invitation tokens"""

    token = serializers.CharField(required=True)


class InvitationAcceptSerializer(serializers.Serializer):
    """Serializer for accepting invitations"""

    token = serializers.CharField(required=True)
