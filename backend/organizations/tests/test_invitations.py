"""
Unit tests for Organization Invitation System

Tests cover:
- Invitation creation by org admins
- Token generation and validation
- Invitation acceptance workflow
- Permission checks
- Email validation and matching
- Expiration handling
- Duplicate invitation prevention
- Role assignment
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from organizations.models import (
    User,
    Organization,
    OrganizationMembership,
    OrganizationInvitation,
)


class OrganizationInvitationModelTests(TestCase):
    """Test OrganizationInvitation model methods and properties"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            password="pass",
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

    def test_token_auto_generation(self):
        """Test that token is automatically generated on save"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertIsNotNone(invitation.token)
        self.assertTrue(len(invitation.token) > 0)

    def test_token_is_unique(self):
        """Test that generated tokens are unique"""
        invitation1 = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test1@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        invitation2 = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test2@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertNotEqual(invitation1.token, invitation2.token)

    def test_expiration_auto_set(self):
        """Test that expiration is automatically set on save"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertIsNotNone(invitation.expires_at)
        self.assertTrue(invitation.expires_at > timezone.now())

    def test_expiration_respects_settings(self):
        """Test that expiration uses INVITATION_EXPIRY_DAYS setting"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        expected_days = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)
        expected_expiration = timezone.now() + timedelta(days=expected_days)

        # Allow for small time difference (1 second)
        time_diff = abs((invitation.expires_at - expected_expiration).total_seconds())
        self.assertLess(time_diff, 1)

    def test_is_valid_for_new_invitation(self):
        """Test that new invitations are valid"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertTrue(invitation.is_valid())
        self.assertFalse(invitation.is_expired())

    def test_is_valid_after_acceptance(self):
        """Test that accepted invitations are not valid"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        invitation.accept()
        self.assertFalse(invitation.is_valid())

    def test_is_expired_for_old_invitation(self):
        """Test that expired invitations are detected"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        # Manually set expiration to past
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save()

        self.assertTrue(invitation.is_expired())
        self.assertFalse(invitation.is_valid())

    def test_accept_method(self):
        """Test accept method sets accepted_at"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertIsNone(invitation.accepted_at)

        invitation.accept()
        self.assertIsNotNone(invitation.accepted_at)
        self.assertTrue(invitation.accepted_at <= timezone.now())

    def test_str_representation_pending(self):
        """Test string representation for pending invitation"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        expected = f"test@example.com -> {self.org.name} (Pending)"
        self.assertEqual(str(invitation), expected)

    def test_str_representation_accepted(self):
        """Test string representation for accepted invitation"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        invitation.accept()
        expected = f"test@example.com -> {self.org.name} (Accepted)"
        self.assertEqual(str(invitation), expected)

    def test_role_choices(self):
        """Test that both role types can be assigned"""
        # Test MEMBER role
        invitation_member = OrganizationInvitation.objects.create(
            organization=self.org,
            email="member@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        self.assertEqual(invitation_member.role, OrganizationInvitation.Role.MEMBER)

        # Test ORG_ADMIN role
        invitation_admin = OrganizationInvitation.objects.create(
            organization=self.org,
            email="admin@example.com",
            role=OrganizationInvitation.Role.ORG_ADMIN,
            invited_by=self.admin_user,
        )
        self.assertEqual(invitation_admin.role, OrganizationInvitation.Role.ORG_ADMIN)


class InvitationCreationAPITests(APITestCase):
    """Test invitation creation via API endpoint"""

    def setUp(self):
        # Create org admin
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            password="pass",
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

        # Create regular member
        self.member_user = User.objects.create_user(
            email="member@example.com",
            username="member",
            password="pass",
        )
        OrganizationMembership.objects.create(
            user=self.member_user,
            organization=self.org,
            role=OrganizationMembership.Role.MEMBER,
        )

        # Create user without org
        self.outsider_user = User.objects.create_user(
            email="outsider@example.com",
            username="outsider",
            password="pass",
        )

    def test_create_invitation_as_admin_success(self):
        """Test org admin can successfully create invitations"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationInvitation.objects.count(), 1)

        # Verify response data
        self.assertIn("id", response.data)
        # Token is not exposed in response for security
        self.assertEqual(response.data["email"], "newuser@example.com")
        self.assertEqual(response.data["role"], "MEMBER")
        self.assertEqual(response.data["organization_name"], self.org.name)

    def test_create_invitation_as_admin_role(self):
        """Test creating invitation with ORG_ADMIN role"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "newadmin@example.com", "role": "ORG_ADMIN"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        invitation = OrganizationInvitation.objects.first()
        self.assertEqual(invitation.role, OrganizationInvitation.Role.ORG_ADMIN)

    def test_create_invitation_requires_admin_permission(self):
        """Test non-admin cannot create invitations"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.member_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OrganizationInvitation.objects.count(), 0)

    def test_create_invitation_requires_authentication(self):
        """Test unauthenticated users cannot create invitations"""
        url = reverse("create-invitation")

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(OrganizationInvitation.objects.count(), 0)

    def test_create_invitation_requires_organization_membership(self):
        """Test user without organization cannot create invitations"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.outsider_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OrganizationInvitation.objects.count(), 0)

    def test_create_invitation_invalid_email(self):
        """Test creating invitation with invalid email"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "not-an-email", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OrganizationInvitation.objects.count(), 0)

    def test_create_invitation_missing_email(self):
        """Test creating invitation without email"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OrganizationInvitation.objects.count(), 0)

    def test_create_invitation_duplicate_pending(self):
        """Test cannot create duplicate pending invitation to same email"""
        # Create first invitation
        OrganizationInvitation.objects.create(
            organization=self.org,
            email="newuser@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valid invitation already exists", str(response.data).lower())
        self.assertEqual(OrganizationInvitation.objects.count(), 1)

    def test_create_invitation_after_previous_accepted(self):
        """Test can create new invitation after previous one was accepted"""
        # Create and accept first invitation
        old_invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="newuser@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        old_invitation.accept()

        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrganizationInvitation.objects.count(), 2)

    def test_create_invitation_tracks_invited_by(self):
        """Test invitation records who sent it"""
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "newuser@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        invitation = OrganizationInvitation.objects.first()
        self.assertEqual(invitation.invited_by, self.admin_user)

    def test_create_invitation_user_already_in_organization(self):
        """Test cannot invite user who already belongs to an organization"""
        # Create another organization and a user who belongs to it
        other_org = Organization.objects.create(
            name="Other Org", status=Organization.Status.APPROVED
        )
        user_with_org = User.objects.create_user(
            email="hasorg@example.com",
            username="hasorg",
            password="pass",
        )
        OrganizationMembership.objects.create(
            user=user_with_org,
            organization=other_org,
            role=OrganizationMembership.Role.MEMBER,
        )

        # Try to invite this user to our org
        url = reverse("create-invitation")
        self.client.force_authenticate(user=self.admin_user)

        data = {"email": "hasorg@example.com", "role": "MEMBER"}
        response = self.client.post(url, data, format="json")

        # Should fail because user already belongs to another org
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "already belongs to an organization", str(response.data["email"][0]).lower()
        )


class InvitationValidationAPITests(APITestCase):
    """Test invitation token validation via API endpoint"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="pass",
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

    def test_validate_valid_token(self):
        """Test validating a valid invitation token"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("validate-invitation")
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["organization_name"], self.org.name)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["role"], "Member")

    def test_validate_invalid_token(self):
        """Test validating an invalid token"""
        url = reverse("validate-invitation")
        data = {"token": "invalid-token-12345"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_validate_expired_token(self):
        """Test validating an expired token"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        # Manually expire the invitation
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save()

        url = reverse("validate-invitation")
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data).lower())

    def test_validate_accepted_token(self):
        """Test validating an already accepted token"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        invitation.accept()

        url = reverse("validate-invitation")
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been accepted", str(response.data))

    def test_validate_token_no_authentication_required(self):
        """Test validation endpoint doesn't require authentication"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="test@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("validate-invitation")
        data = {"token": invitation.token}
        # Not authenticating
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])

    def test_validate_missing_token(self):
        """Test validation without providing token"""
        url = reverse("validate-invitation")
        data = {}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InvitationAcceptanceAPITests(APITestCase):
    """Test invitation acceptance via API endpoint"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="pass",
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

        self.invited_user = User.objects.create_user(
            email="invited@example.com",
            username="invited",
            password="pass",
        )

    def test_accept_invitation_success(self):
        """Test successfully accepting an invitation"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify membership created
        membership = OrganizationMembership.objects.get(
            user=self.invited_user, organization=self.org
        )
        self.assertEqual(membership.role, OrganizationMembership.Role.MEMBER)

        # Verify invitation marked as accepted
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)

    def test_accept_invitation_as_admin(self):
        """Test accepting invitation with ORG_ADMIN role"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.ORG_ADMIN,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        membership = OrganizationMembership.objects.get(
            user=self.invited_user, organization=self.org
        )
        self.assertEqual(membership.role, OrganizationMembership.Role.ORG_ADMIN)

    def test_accept_invitation_requires_authentication(self):
        """Test accepting invitation requires authentication"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accept_invitation_email_mismatch(self):
        """Test cannot accept invitation with wrong email"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="different@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email mismatch", response.data["error"])

        # Verify no membership created
        self.assertFalse(
            OrganizationMembership.objects.filter(
                user=self.invited_user, organization=self.org
            ).exists()
        )

    def test_accept_expired_invitation(self):
        """Test cannot accept expired invitation"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.save()

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data).lower())

    def test_accept_invitation_twice(self):
        """Test cannot accept same invitation twice"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}

        # Accept first time
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try to accept again (as same user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been accepted", response.data["error"])

    def test_accept_invitation_invalid_token(self):
        """Test accepting with invalid token"""
        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": "invalid-token-12345"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invitation_missing_token(self):
        """Test accepting without providing token"""
        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invitation_user_already_in_org(self):
        """Test user already in organization cannot accept invitation"""
        # User already has membership
        OrganizationMembership.objects.create(
            user=self.invited_user,
            organization=self.org,
            role=OrganizationMembership.Role.MEMBER,
        )

        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="invited@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        url = reverse("accept-invitation")
        self.client.force_authenticate(user=self.invited_user)
        data = {"token": invitation.token}
        response = self.client.post(url, data, format="json")

        # Should fail because user already has membership
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already belong to an organization", str(response.data).lower())


class InvitationEmailTests(TestCase):
    """Test invitation email sending functionality"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            password="pass",
        )
        self.org = Organization.objects.create(
            name="Test Org", status=Organization.Status.APPROVED
        )
        OrganizationMembership.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

    def test_invitation_email_sent_on_creation(self):
        """Test that email is sent when invitation is created via API"""
        from django.core import mail

        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="newuser@example.com",
            role=OrganizationInvitation.Role.MEMBER,
            invited_by=self.admin_user,
        )

        # Import and call email function
        from organizations.emails import send_invitation_token_email

        send_invitation_token_email(invitation)

        # Check that one message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify email details
        email = mail.outbox[0]
        self.assertEqual(email.to, ["newuser@example.com"])
        self.assertIn(self.org.name, email.subject)
        self.assertIn(invitation.token, email.body)
