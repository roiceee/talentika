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
    is_org_admin,
    get_user_organizations,
)
from .serializers import (
    UserSerializer,
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationListSerializer,
    OrganizationApprovalSerializer,
    OrganizationMembershipSerializer,
)
from .emails import send_invitation_email


# ============= User Registration =============


@swagger_auto_schema(
    method="post",
    operation_description="Register a new user account. This is the first step - users must create an account before creating organizations.",
    request_body=UserSerializer,
    responses={
        201: openapi.Response("User created successfully", UserSerializer),
        400: "Validation error",
    },
    tags=["Users"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user account.
    Users must create an account first before they can create organizations.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============= Organization Management =============


@swagger_auto_schema(
    method="get",
    operation_description="List all organizations the authenticated user belongs to.",
    responses={200: OrganizationListSerializer(many=True)},
    tags=["Organizations"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_organizations(request):
    """
    List all organizations the authenticated user belongs to.
    """
    organizations = get_user_organizations(request.user)
    serializer = OrganizationListSerializer(organizations, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Create a new organization. The authenticated user becomes the organization admin.
    Organization starts with PENDING status and must be approved by a super admin.
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
    - Sets status to PENDING
    - Creates OrganizationMembership with ORG_ADMIN role for the creator
    - Pending organizations cannot invite users or access protected features

    TODO: Send notification email to super admins about new pending organization
    """
    serializer = OrganizationCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Create organization with PENDING status (default)
        organization = serializer.save()

        # Create membership with ORG_ADMIN role for the creator
        OrganizationMembership.objects.create(
            user=request.user,
            organization=organization,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

        # TODO: Send email notification to super admins
        # send_new_organization_notification(organization)

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
    request_body=OrganizationCreateSerializer(partial=True),
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


# ============= Admin Approval Endpoints =============


@swagger_auto_schema(
    method="get",
    operation_description="List all pending organizations. Super admin only.",
    responses={
        200: OrganizationListSerializer(many=True),
        403: "Super admin access required",
    },
    tags=["Admin"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_pending_organizations(request):
    """
    List all pending organizations waiting for approval.
    Super admin only.
    """
    if not request.user.is_superuser:
        return Response(
            {"error": "Super admin access required."}, status=status.HTTP_403_FORBIDDEN
        )

    pending_orgs = Organization.objects.filter(status=Organization.Status.PENDING)
    serializer = OrganizationListSerializer(pending_orgs, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    operation_description="""
    Approve, reject, or suspend an organization. Super admin only.
    Actions:
    - approve: Change status from PENDING to APPROVED
    - reject: Change status from PENDING to REJECTED
    - suspend: Change status from APPROVED to SUSPENDED
    """,
    request_body=OrganizationApprovalSerializer,
    responses={
        200: openapi.Response("Action completed successfully", OrganizationSerializer),
        400: "Invalid action for current status",
        403: "Super admin access required",
        404: "Organization not found",
    },
    tags=["Admin"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manage_organization_status(request, org_id):
    """
    Approve, reject, or suspend an organization.
    Super admin only.

    Actions:
    - approve: Sets status to APPROVED, records approval timestamp and admin
    - reject: Sets status to REJECTED
    - suspend: Sets status to SUSPENDED (for approved organizations)

    TODO: Send email notifications to organization admins about status changes
    """
    if not request.user.is_superuser:
        return Response(
            {"error": "Super admin access required."}, status=status.HTTP_403_FORBIDDEN
        )

    organization = get_object_or_404(Organization, id=org_id)

    serializer = OrganizationApprovalSerializer(
        data=request.data, context={"organization": organization}
    )

    if serializer.is_valid():
        action = serializer.validated_data["action"]

        if action == "approve":
            organization.approve(request.user)
            message = f"Organization '{organization.name}' has been approved."
            # TODO: send_approval_notification(organization)
        elif action == "reject":
            organization.reject()
            message = f"Organization '{organization.name}' has been rejected."
            # TODO: send_rejection_notification(organization)
        elif action == "suspend":
            organization.suspend()
            message = f"Organization '{organization.name}' has been suspended."
            # TODO: send_suspension_notification(organization)

        response_serializer = OrganizationSerializer(organization)
        return Response({"message": message, "organization": response_serializer.data})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============= Organization Membership =============


@swagger_auto_schema(
    method="get",
    operation_description="List all members of an organization.",
    responses={
        200: OrganizationMembershipSerializer(many=True),
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


@swagger_auto_schema(
    method="post",
    operation_description="""
    Invite a user to join the organization. Only available for approved organizations.
    Only organization admins can invite users.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["user_id", "role"],
        properties={
            "user_id": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="ID of user to invite"
            ),
            "role": openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=["ORG_ADMIN", "MEMBER"],
                description="Role for the user",
            ),
        },
    ),
    responses={
        201: OrganizationMembershipSerializer,
        400: "Validation error or organization not approved",
        403: "Only organization admins can invite users",
        404: "Organization or user not found",
    },
    tags=["Organizations"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invite_user_to_organization(request, org_id):
    """
    Invite a user to join the organization.
    - Only approved organizations can invite users
    - Only organization admins can invite
    - Cannot invite user who is already a member
    - Sends invitation email to the user
    """
    organization = get_object_or_404(Organization, id=org_id)

    # Check if organization is approved
    if not organization.is_approved():
        return Response(
            {"error": "Only approved organizations can invite users."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user is org admin
    if not is_org_admin(request.user, organization):
        return Response(
            {"error": "Only organization admins can invite users."},
            status=status.HTTP_403_FORBIDDEN,
        )

    user_id = request.data.get("user_id")
    role = request.data.get("role", OrganizationMembership.Role.MEMBER)

    # Get the user to invite
    user_to_invite = get_object_or_404(User, id=user_id)

    # Check if user is already a member
    if organization.memberships.filter(user=user_to_invite).exists():
        return Response(
            {"error": "User is already a member of this organization."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create membership
    membership = OrganizationMembership.objects.create(
        user=user_to_invite, organization=organization, role=role
    )

    # Send invitation email
    email_sent = send_invitation_email(user_to_invite, organization, request.user)

    serializer = OrganizationMembershipSerializer(membership)
    response_data = {**serializer.data, "email_sent": email_sent}
    return Response(response_data, status=status.HTTP_201_CREATED)
