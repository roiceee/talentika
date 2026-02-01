from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import (
    User,
    Organization,
    OrganizationMembership,
    is_org_admin,
    get_user_organizations,
)


class UserRegistrationTests(APITestCase):
    """Test user registration"""

    def test_register_user_success(self):
        """Test successful user registration"""
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_register_user_password_mismatch(self):
        """Test registration fails with password mismatch"""
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email"""
        User.objects.create_user(
            email="testuser@example.com",
            username="testuser1",
            password="SecurePass123!",
        )
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser2",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTests(APITestCase):
    """Test JWT authentication with email"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="SecurePass123!",
        )

    def test_login_with_email(self):
        """Test login using email instead of username"""
        url = reverse("token-obtain")
        data = {"email": "testuser@example.com", "password": "SecurePass123!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        url = reverse("token-obtain")
        data = {"email": "testuser@example.com", "password": "WrongPassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
        """Test new organizations start with PENDING status"""
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
        """Test creating organization creates it as PENDING and adds creator as admin"""
        url = reverse("create-organization")
        data = {"name": "New Org", "address": "123 Test St"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 1)

        org = Organization.objects.first()
        self.assertEqual(org.status, Organization.Status.PENDING)

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

    def test_get_user_organizations(self):
        """Test getting organizations for a user"""
        orgs = get_user_organizations(self.admin_user)
        self.assertEqual(orgs.count(), 1)
        self.assertIn(self.org, orgs)

        orgs = get_user_organizations(self.outsider_user)
        self.assertEqual(orgs.count(), 0)

    def test_invite_user_requires_admin(self):
        """Test only org admins can invite users"""
        url = reverse("invite-user", kwargs={"org_id": self.org.id})
        data = {"user_id": self.outsider_user.id, "role": "MEMBER"}

        # Admin can invite
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Regular member cannot invite
        self.client.force_authenticate(user=self.member_user)
        new_user = User.objects.create_user(
            email="another@example.com", username="another", password="pass"
        )
        data = {"user_id": new_user.id, "role": "MEMBER"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
        self.pending_org = Organization.objects.create(
            name="Pending Org", status=Organization.Status.PENDING
        )
        self.approved_org = Organization.objects.create(
            name="Approved Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.user, organization=self.pending_org
        )
        OrganizationMembership.objects.create(
            user=self.user, organization=self.approved_org
        )

    def test_get_user_organizations_by_status(self):
        """Test filtering user organizations by status"""
        pending_orgs = get_user_organizations(
            self.user, status=Organization.Status.PENDING
        )
        self.assertEqual(pending_orgs.count(), 1)
        self.assertIn(self.pending_org, pending_orgs)

        approved_orgs = get_user_organizations(
            self.user, status=Organization.Status.APPROVED
        )
        self.assertEqual(approved_orgs.count(), 1)
        self.assertIn(self.approved_org, approved_orgs)
