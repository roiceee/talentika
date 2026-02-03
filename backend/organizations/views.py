from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    User,
    Organization,
    OrganizationMembership,
    OrganizationInvitation,
    is_org_admin,
)
from .serializers import (
    UserSerializer,
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationListSerializer,
    OrganizationApprovalSerializer,
    OrganizationMembershipSerializer,
    OrganizationInvitationSerializer,
    InvitationCreateSerializer,
    InvitationValidateSerializer,
    InvitationAcceptSerializer,
)
from .emails import send_invitation_token_email
from .permissions import IsOrgAdminOfOwnOrganization, IsOrganizationMember


# ============= User Registration =============


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


# ============= Organization Management =============


@swagger_auto_schema(
    method="get",
    operation_description="Get all organizations the authenticated user belongs to. Users can belong to multiple organizations.",
    responses={
        200: OrganizationListSerializer(many=True),
        404: "User does not belong to any organization",
    },
    tags=["Organizations"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_organizations(request):
    """
    Get all organizations the authenticated user belongs to.
    Users can belong to multiple organizations.
    """
    memberships = OrganizationMembership.objects.filter(
        user=request.user
    ).select_related("organization")

    if not memberships.exists():
        return Response(
            {"error": "You do not belong to any organization."},
            status=status.HTTP_404_NOT_FOUND,
        )

    organizations = [membership.organization for membership in memberships]
    serializer = OrganizationListSerializer(organizations, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Create a new organization. The authenticated user becomes the organization admin.
    Organization is automatically approved upon creation.
    """,
    request_body=OrganizationCreateSerializer,
    responses={
        201: openapi.Response(
            "Organization created successfully", OrganizationSerializer
        ),
        400: "Validation error",
    },
    tags=["Organizations"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_organization(request):
    """
    Create a new organization.
    - Organization is automatically approved (APPROVED status)
    - Creates OrganizationMembership with ORG_ADMIN role for the creator
    - Creator can immediately invite users and access all features
    - Users can belong to multiple organizations
    """
    serializer = OrganizationCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Create organization with APPROVED status
        organization = serializer.save(status=Organization.Status.APPROVED)

        # Create membership with ORG_ADMIN role for the creator
        OrganizationMembership.objects.create(
            user=request.user,
            organization=organization,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

        # Return full organization details
        response_serializer = OrganizationSerializer(organization)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    operation_description="Get detailed information about a specific organization.",
    responses={
        200: OrganizationSerializer,
        403: "User is not a member of this organization",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_organization(request, org_id):
    """
    Get detailed information about a specific organization.
    User must be a member of the organization to view details.
    """
    organization = get_object_or_404(Organization, id=org_id)

    # Check if user is a member (or superuser)
    if not request.user.is_superuser:
        if not organization.memberships.filter(user=request.user).exists():
            return Response(
                {"error": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = OrganizationSerializer(organization)
    return Response(serializer.data)


@swagger_auto_schema(
    method="patch",
    operation_description="Update organization details. Only organization admins can update.",
    request_body=OrganizationCreateSerializer,
    responses={
        200: OrganizationSerializer,
        403: "User is not an admin of this organization",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_organization(request, org_id):
    """
    Update organization details (name, address).
    Only organization admins can update.
    Status and approval fields cannot be updated via this endpoint.
    """
    organization = get_object_or_404(Organization, id=org_id)

    # Check if user is org admin
    if not is_org_admin(request.user, organization):
        return Response(
            {"error": "Only organization admins can update organization details."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = OrganizationCreateSerializer(
        organization, data=request.data, partial=True
    )
    if serializer.is_valid():
        serializer.save()
        response_serializer = OrganizationSerializer(organization)
        return Response(response_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============= Organization Membership =============


@swagger_auto_schema(
    method="get",
    operation_description="List all members of an organization.",
    responses={
        200: openapi.Response(
            "List of organization members",
            OrganizationMembershipSerializer(many=True),
        ),
        403: "User is not a member of this organization",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_organization_members(request, org_id):
    """
    List all members of an organization.
    User must be a member of the organization.
    """
    organization = get_object_or_404(Organization, id=org_id)

    # Check if user is a member (or superuser)
    if not request.user.is_superuser:
        if not organization.memberships.filter(user=request.user).exists():
            return Response(
                {"error": "You are not a member of this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

    memberships = organization.memberships.select_related("user").all()
    serializer = OrganizationMembershipSerializer(memberships, many=True)
    return Response(serializer.data)


# ============= Organization Invitations =============


@swagger_auto_schema(
    method="post",
    operation_description="""
    Create an invitation to join the organization.
    Only org admins of APPROVED organizations can send invitations.
    Invitation link will be sent to the specified email address.
    
    The email contains a secure, single-use token that expires after 7 days.
    The link points to the frontend application which handles the acceptance flow.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="UUID of the organization",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    request_body=InvitationCreateSerializer,
    responses={
        201: openapi.Response(
            "Invitation created and email sent", OrganizationInvitationSerializer
        ),
        400: "Validation error or organization not approved",
        403: "Only organization admins can send invitations",
        404: "Organization not found",
    },
    tags=["Invitations"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrgAdminOfOwnOrganization])
def create_invitation(request, org_id):
    """
    Create an invitation to join the organization.

    Business Rules:
    - Only org admins can create invitations
    - Organization must be APPROVED
    - Cannot invite users who are already members of this specific organization
    - Cannot create duplicate pending invitations for same email
    - Invitation expires after configured time (default: 7 days)

    Front-end Integration:
    - Email contains URL like: https://app.example.com/invite/accept?token=...
    - Front-end should:
      1. Call POST /api/invitations/validate/ to check token
      2. Show invitation details to user
      3. Prompt user to sign in/sign up with matching email
      4. Call POST /api/invitations/accept/ to complete acceptance
    """
    # Get the organization and verify user is admin
    try:
        organization = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response(
            {"error": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if user is admin of this organization
    if not is_org_admin(request.user, organization):
        return Response(
            {"error": "Only organization admins can send invitations."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check if organization is approved
    if organization.status != Organization.Status.APPROVED:
        return Response(
            {"error": "Only approved organizations can send invitations."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate input
    serializer = InvitationCreateSerializer(
        data=request.data, context={"organization": organization}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Create invitation
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=serializer.validated_data["email"].lower().strip(),
        role=serializer.validated_data.get("role", OrganizationInvitation.Role.MEMBER),
        invited_by=request.user,
    )

    # Send invitation email
    # TODO: In production, consider using task queue (Celery) for async email sending
    email_sent = send_invitation_token_email(invitation)

    # Return invitation details
    response_serializer = OrganizationInvitationSerializer(invitation)
    response_data = {**response_serializer.data, "email_sent": email_sent}
    return Response(response_data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method="get",
    operation_description="""
    List all invitations for the organization.
    Shows both pending and accepted invitations.
    Only organization members can view invitations.
    """,
    manual_parameters=[
        openapi.Parameter(
            "org_id",
            openapi.IN_PATH,
            description="UUID of the organization",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            "List of invitations", OrganizationInvitationSerializer(many=True)
        ),
        403: "Only organization members can view invitations",
        404: "Organization not found",
    },
    tags=["Invitations"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def list_organization_invitations(request, org_id):
    """
    List all invitations for the organization.

    Returns both pending and accepted invitations with details including:
    - Email address
    - Role
    - Invited by
    - Status (accepted/pending)
    - Expiration date
    """
    organization = get_object_or_404(Organization, id=org_id)

    invitations = (
        OrganizationInvitation.objects.filter(organization=organization)
        .select_related("invited_by")
        .order_by("-created_at")
    )

    serializer = OrganizationInvitationSerializer(invitations, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Validate an invitation token without accepting it.
    This endpoint is public (no authentication required).
    
    Use this to display invitation details to the user before they accept.
    Returns organization info, role, and invitation status.
    """,
    request_body=InvitationValidateSerializer,
    responses={
        200: openapi.Response(
            "Invitation is valid",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "valid": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "organization_name": openapi.Schema(type=openapi.TYPE_STRING),
                    "role": openapi.Schema(type=openapi.TYPE_STRING),
                    "email": openapi.Schema(type=openapi.TYPE_STRING),
                    "invited_by": openapi.Schema(type=openapi.TYPE_STRING),
                    "expires_at": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        400: "Invalid, expired, or already accepted token",
    },
    tags=["Invitations"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def validate_invitation(request):
    """
    Validate an invitation token.

    This is a public endpoint that allows the front-end to check if a token is valid
    before requiring the user to sign in/sign up.

    Returns invitation metadata if valid, or error if:
    - Token doesn't exist
    - Token has expired
    - Invitation already accepted
    """
    serializer = InvitationValidateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data["token"]

    try:
        invitation = OrganizationInvitation.objects.get(token=token)
    except OrganizationInvitation.DoesNotExist:
        return Response(
            {"error": "Invalid invitation token."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if already accepted
    if invitation.accepted_at:
        return Response(
            {"error": "This invitation has already been accepted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if expired
    if invitation.is_expired():
        return Response(
            {"error": "This invitation has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Return invitation details
    return Response(
        {
            "valid": True,
            "organization_name": invitation.organization.name,
            "organization_id": str(invitation.organization.id),
            "role": invitation.get_role_display(),
            "email": invitation.email,
            "invited_by": invitation.invited_by.get_full_name(),
            "invited_by_email": invitation.invited_by.email,
            "expires_at": invitation.expires_at.isoformat(),
        }
    )


@swagger_auto_schema(
    method="post",
    operation_description="""
    Accept an invitation to join an organization.
    Requires authentication - user must be signed in.
    
    Validation:
    - Token must be valid (not expired, not already accepted)
    - Logged-in user's email must match invitation email
    - User must not already be a member of this specific organization
    
    On success:
    - Creates OrganizationMembership
    - Marks invitation as accepted
    - Returns success response with membership details
    """,
    request_body=InvitationAcceptSerializer,
    responses={
        200: openapi.Response(
            "Invitation accepted successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "organization": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="Organization details",
                    ),
                    "membership": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="Membership details",
                    ),
                },
            ),
        ),
        400: "Invalid token, email mismatch, or user already in organization",
        401: "Authentication required",
    },
    tags=["Invitations"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_invitation(request):
    """
    Accept an invitation to join an organization.

    Business Rules:
    - User must be authenticated
    - User's email must match invitation email (case-insensitive)
    - User cannot already be a member of this specific organization
    - Token must be valid (not expired, not already accepted)

    On success:
    - Creates OrganizationMembership with specified role
    - Marks invitation as accepted
    - Returns organization and membership details
    """
    serializer = InvitationAcceptSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data["token"]

    # Get invitation
    try:
        invitation = OrganizationInvitation.objects.select_related(
            "organization", "invited_by"
        ).get(token=token)
    except OrganizationInvitation.DoesNotExist:
        return Response(
            {"error": "Invalid invitation token."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if already accepted
    if invitation.accepted_at:
        return Response(
            {"error": "This invitation has already been accepted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if expired
    if invitation.is_expired():
        return Response(
            {"error": "This invitation has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify email match
    if request.user.email.lower() != invitation.email.lower():
        return Response(
            {
                "error": f"Email mismatch. This invitation is for {invitation.email}, but you are signed in as {request.user.email}."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user is already a member of this organization
    if OrganizationMembership.objects.filter(
        user=request.user, organization=invitation.organization
    ).exists():
        return Response(
            {"error": "You are already a member of this organization."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create membership
    membership = OrganizationMembership.objects.create(
        user=request.user, organization=invitation.organization, role=invitation.role
    )

    # Mark invitation as accepted
    invitation.accept()

    # Return success response
    org_serializer = OrganizationSerializer(invitation.organization)
    membership_serializer = OrganizationMembershipSerializer(membership)

    return Response(
        {
            "message": f"Successfully joined {invitation.organization.name}!",
            "organization": org_serializer.data,
            "membership": membership_serializer.data,
        }
    )
