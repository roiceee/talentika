from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Organization, OrganizationMembership
from ..serializers import OrganizationMembershipSerializer
from ..permissions import IsOrganizationMember, IsOrganizationAdmin


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


@swagger_auto_schema(
    method="delete",
    operation_description="""
    Remove a member from the organization.
    Only organization admins can remove members.
    Cannot remove the last admin from the organization.
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
        openapi.Parameter(
            "membership_id",
            openapi.IN_PATH,
            description="UUID of the membership to remove",
            type=openapi.TYPE_STRING,
            format="uuid",
            required=True,
        ),
    ],
    responses={
        204: "Member removed successfully",
        400: "Cannot remove the last admin",
        403: "Only organization admins can remove members",
        404: "Organization or membership not found",
    },
    tags=["Organizations"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsOrganizationAdmin])
def remove_member(request, org_id, membership_id):
    """
    Remove a member from the organization.

    Rules:
    - Only org admins can remove members
    - Cannot remove the last admin (must have at least one admin)
    """
    organization = get_object_or_404(Organization, id=org_id)
    membership = get_object_or_404(
        OrganizationMembership, id=membership_id, organization=organization
    )

    # Check if removing the last admin
    if membership.role == OrganizationMembership.Role.ORG_ADMIN:
        admin_count = OrganizationMembership.objects.filter(
            organization=organization, role=OrganizationMembership.Role.ORG_ADMIN
        ).count()
        if admin_count <= 1:
            return Response(
                {"error": "Cannot remove the last admin from the organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    membership.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method="delete",
    operation_description="""
    Leave the organization.
    Any member can leave the organization.
    Admins can only leave if there is at least one other admin.
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
        204: "Successfully left the organization",
        400: "Cannot leave - you are the last admin",
        403: "You are not a member of this organization",
        404: "Organization not found",
    },
    tags=["Organizations"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsOrganizationMember])
def leave_organization(request, org_id):
    """
    Leave the organization.

    Rules:
    - Any member can leave
    - Admins can only leave if there is at least one other admin
    """
    organization = get_object_or_404(Organization, id=org_id)

    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization
        )
    except OrganizationMembership.DoesNotExist:
        return Response(
            {"error": "You are not a member of this organization."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # If user is admin, check if they are the last admin
    if membership.role == OrganizationMembership.Role.ORG_ADMIN:
        admin_count = OrganizationMembership.objects.filter(
            organization=organization, role=OrganizationMembership.Role.ORG_ADMIN
        ).count()
        if admin_count <= 1:
            return Response(
                {
                    "error": "Cannot leave the organization. You are the last admin. Please assign another admin before leaving."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    membership.delete()
    return Response(
        {"message": f"You have successfully left {organization.name}."},
        status=status.HTTP_200_OK,
    )
