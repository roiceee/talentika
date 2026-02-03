"""
Unit tests for Organization model and management

Tests cover:
- Organization creation and status management
- Organization approval workflow
- User membership and permissions
- Super admin access control
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from organizations.models import (
    User,
    Organization,
    OrganizationMembership,
    is_org_admin,
    get_user_organization,
)


class OrganizationModelTests(TestCase):
    """Test Organization model methods"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", username="testuser", password="pass"
        )
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.org = Organization.objects.create(name="Test Org")

    def test_organization_starts_as_pending(self):
        """Test organizations created directly via model start with PENDING status by default"""
        self.assertEqual(self.org.status, Organization.Status.PENDING)
        self.assertFalse(self.org.is_approved())

    def test_approve_organization(self):
        """Test approving organization"""
        self.org.approve(self.superuser)
        self.assertEqual(self.org.status, Organization.Status.APPROVED)
        self.assertTrue(self.org.is_approved())
        self.assertIsNotNone(self.org.approved_at)
        self.assertEqual(self.org.approved_by, self.superuser)

    def test_reject_organization(self):
        """Test rejecting organization"""
        self.org.reject()
        self.assertEqual(self.org.status, Organization.Status.REJECTED)
        self.assertFalse(self.org.is_approved())

    def test_can_invite_users_approved_only(self):
        """Test only approved organizations can invite users"""
        self.assertFalse(self.org.can_invite_users())
        self.org.approve(self.superuser)
        self.assertTrue(self.org.can_invite_users())


class OrganizationCreationTests(APITestCase):
    """Test organization creation via API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", username="testuser", password="pass"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_organization(self):
        """Test creating organization via API creates it as APPROVED and adds creator as admin"""
        url = reverse("create-organization")
        data = {"name": "New Org", "address": "123 Test St"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 1)

        org = Organization.objects.first()
        self.assertEqual(org.status, Organization.Status.APPROVED)
        self.assertTrue(org.is_approved())

        # Check membership was created with ORG_ADMIN role
        membership = OrganizationMembership.objects.get(
            user=self.user, organization=org
        )
        self.assertEqual(membership.role, OrganizationMembership.Role.ORG_ADMIN)

    def test_create_organization_unauthenticated(self):
        """Test creating organization requires authentication"""
        self.client.force_authenticate(user=None)
        url = reverse("create-organization")
        data = {"name": "New Org"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrganizationMembershipTests(APITestCase):
    """Test organization membership and permissions"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com", username="admin", password="pass"
        )
        self.member_user = User.objects.create_user(
            email="member@example.com", username="member", password="pass"
        )
        self.outsider_user = User.objects.create_user(
            email="outsider@example.com", username="outsider", password="pass"
        )
        self.superuser = User.objects.create_superuser(
            email="super@example.com", username="super", password="pass"
        )

        # Create approved organization
        self.org = Organization.objects.create(name="Test Org")
        self.org.approve(self.superuser)

        # Add memberships
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )
        OrganizationMembership.objects.create(
            user=self.member_user,
            organization=self.org,
            role=OrganizationMembership.Role.MEMBER,
        )

    def test_is_org_admin_helper(self):
        """Test is_org_admin helper function"""
        self.assertTrue(is_org_admin(self.admin_user, self.org))
        self.assertFalse(is_org_admin(self.member_user, self.org))
        self.assertTrue(
            is_org_admin(self.superuser, self.org)
        )  # Superuser is always admin

    def test_get_user_organization(self):
        """Test getting organization for a user"""
        org = get_user_organization(self.admin_user)
        self.assertIsNotNone(org)
        self.assertEqual(org, self.org)

        org = get_user_organization(self.outsider_user)
        self.assertIsNone(org)

    def test_list_members_requires_membership(self):
        """Test only members can list organization members"""
        url = reverse("list-members", kwargs={"org_id": self.org.id})

        # Member can list
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Outsider cannot list
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SuperAdminTests(APITestCase):
    """Test super admin organization management"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com", username="user", password="pass"
        )
        self.pending_org = Organization.objects.create(name="Pending Org")

    def test_list_pending_organizations_requires_superuser(self):
        """Test only superusers can list pending organizations"""
        url = reverse("list-pending-organizations")

        # Regular user cannot access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Superuser can access
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_approve_organization_requires_superuser(self):
        """Test only superusers can approve organizations"""
        url = reverse(
            "manage-organization-status", kwargs={"org_id": self.pending_org.id}
        )
        data = {"action": "approve"}

        # Regular user cannot approve
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Superuser can approve
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.pending_org.refresh_from_db()
        self.assertEqual(self.pending_org.status, Organization.Status.APPROVED)


class OrganizationPermissionTests(TestCase):
    """Test permission helper functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", username="user", password="pass"
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(user=self.user, organization=self.org)

    def test_get_user_organization(self):
        """Test getting the user's organization"""
        org = get_user_organization(self.user)
        self.assertEqual(org, self.org)

        # Test user with no organization
        new_user = User.objects.create_user(
            email="newuser@example.com", username="newuser", password="pass"
        )
        org = get_user_organization(new_user)
        self.assertIsNone(org)
