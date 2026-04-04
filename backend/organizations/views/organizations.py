from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Organization, OrganizationMembership, is_org_admin
from ..serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationListSerializer,
)


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
        user=request.user,
        organization__deleted_at__isnull=True,
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

        # Auto-set as default if the user has no default organization yet
        if request.user.default_organization is None:
            request.user.default_organization = organization
            request.user.save(update_fields=["default_organization"])

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


@swagger_auto_schema(
    method="delete",
    operation_description="Soft-delete an organization. Only organization admins can perform this action. This action is irreversible.",
    responses={
        204: "Organization deleted successfully",
        403: "Only organization admins can delete the organization",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_organization(request, org_id):
    """
    Soft-delete an organization.

    Sets deleted_at so the organization is hidden from all queries.
    Only organization admins can perform this action.
    """
    organization = get_object_or_404(Organization, id=org_id)

    if not is_org_admin(request.user, organization):
        return Response(
            {"error": "Only organization admins can delete the organization."},
            status=status.HTTP_403_FORBIDDEN,
        )

    organization.deleted_at = timezone.now()
    organization.save(update_fields=["deleted_at"])
    return Response(status=status.HTTP_204_NO_CONTENT)
