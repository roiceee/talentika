"""
Integration tests — Organization onboarding flow

Covers the full sequence:
  Admin registers → Creates org → Superadmin approves →
  Admin invites member → Member registers → Member accepts invitation →
  Both can access org data → Admin removes member
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User
from organizations.models import Organization, OrganizationMembership


class OrgOnboardingFlowTests(APITestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="super@example.com", username="super", password="pass"
        )

    def test_full_org_onboarding_flow(self):
        # 1. Admin registers
        self.client.post(
            reverse("register"),
            {
                "email": "admin@example.com",
                "username": "orgadmin",
                "first_name": "Org",
                "last_name": "Admin",
                "password": "AdminPass123!",
                "password_confirm": "AdminPass123!",
            },
            format="json",
        )

        # 2. Admin logs in
        login_resp = self.client.post(
            reverse("login"),
            {"email": "admin@example.com", "password": "AdminPass123!"},
            format="json",
        )
        admin_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")

        # 3. Admin creates organization (starts as PENDING)
        create_org_resp = self.client.post(
            reverse("create-organization"),
            {"name": "Acme Corp"},
            format="json",
        )
        self.assertEqual(create_org_resp.status_code, status.HTTP_201_CREATED)
        org_id = create_org_resp.data["id"]

        org = Organization.objects.get(id=org_id)

        # 4. Superadmin approves the organization
        org.approve(self.superuser)
        org.refresh_from_db()
        self.assertTrue(org.is_approved())

        # 5. Admin sends invitation to new member
        invite_resp = self.client.post(
            reverse("create-invitation", kwargs={"org_id": org_id}),
            {"email": "member@example.com", "role": "MEMBER"},
            format="json",
        )
        self.assertEqual(invite_resp.status_code, status.HTTP_201_CREATED)
        invitation_token = org.invitations.filter(
            email="member@example.com"
        ).first().token

        # 6. New member registers
        self.client.credentials()
        self.client.post(
            reverse("register"),
            {
                "email": "member@example.com",
                "username": "newmember",
                "first_name": "New",
                "last_name": "Member",
                "password": "MemberPass123!",
                "password_confirm": "MemberPass123!",
            },
            format="json",
        )

        # 7. Member logs in and accepts invitation
        member_login = self.client.post(
            reverse("login"),
            {"email": "member@example.com", "password": "MemberPass123!"},
            format="json",
        )
        member_token = member_login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {member_token}")

        accept_resp = self.client.post(
            reverse("accept-invitation"),
            {"token": invitation_token},
            format="json",
        )
        self.assertEqual(accept_resp.status_code, status.HTTP_200_OK)

        # 8. Member can now access the organization
        org_resp = self.client.get(
            reverse("get-organization", kwargs={"org_id": org_id})
        )
        self.assertEqual(org_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(org_resp.data["name"], "Acme Corp")

        # Verify membership was created
        member_user = User.objects.get(email="member@example.com")
        self.assertTrue(
            OrganizationMembership.objects.filter(
                user=member_user, organization=org
            ).exists()
        )

        # 9. Admin removes the member
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
        membership = OrganizationMembership.objects.get(
            user=member_user, organization=org
        )
        remove_resp = self.client.delete(
            reverse(
                "remove-member",
                kwargs={"org_id": org_id, "membership_id": membership.id},
            )
        )
        self.assertEqual(remove_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OrganizationMembership.objects.filter(
                user=member_user, organization=org
            ).exists()
        )

    def test_member_cannot_access_other_org(self):
        # Create and approve two separate orgs
        user_a = User.objects.create_user(
            email="a@example.com", username="usera", password="pass"
        )
        user_b = User.objects.create_user(
            email="b@example.com", username="userb", password="pass"
        )

        org_a = Organization.objects.create(name="Org A")
        org_a.approve(self.superuser)
        org_b = Organization.objects.create(name="Org B")
        org_b.approve(self.superuser)

        OrganizationMembership.objects.create(
            user=user_a, organization=org_a, role=OrganizationMembership.Role.MEMBER
        )
        OrganizationMembership.objects.create(
            user=user_b, organization=org_b, role=OrganizationMembership.Role.MEMBER
        )

        # user_a tries to access org_b's job profiles
        self.client.force_authenticate(user=user_a)
        response = self.client.get(
            reverse("list-organization-job-profiles", kwargs={"org_id": org_b.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
