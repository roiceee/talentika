"""
Unit tests for Job Profile app.

Tests cover:
- JobProfile model creation and soft delete
- Job profile API: list, create, get, delete
- Permission checks (admin vs member)
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User
from organizations.models import Organization, OrganizationMembership
from job_profile.models import JobCategory, ExperienceLevel, JobProfile


def make_user(email, username="user"):
    return User.objects.create_user(email=email, username=username, password="pass")


def make_approved_org(superuser, name="Test Org"):
    org = Organization.objects.create(name=name)
    org.approve(superuser)
    return org


def make_member(user, org, role=OrganizationMembership.Role.MEMBER):
    OrganizationMembership.objects.create(user=user, organization=org, role=role)


def make_job_profile(org, user, category, level, title="Software Engineer"):
    return JobProfile.objects.create(
        organization=org,
        created_by=user,
        title=title,
        category=category,
        experience_level=level,
        description="A test job profile.",
        employment_type=JobProfile.EmploymentType.FULL_TIME,
    )


class JobProfileModelTests(TestCase):
    """Test JobProfile model behaviour"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.user = make_user("member@example.com", "member")
        self.org = make_approved_org(self.superuser)
        self.category = JobCategory.objects.create(title="Engineering")
        self.level = ExperienceLevel.objects.create(title="Mid-Level")

    def test_job_profile_creation(self):
        profile = make_job_profile(self.org, self.user, self.category, self.level)
        self.assertEqual(profile.title, "Software Engineer")
        self.assertTrue(profile.is_active)
        self.assertIsNone(profile.deleted_at)

    def test_soft_delete_hides_from_default_manager(self):
        from django.utils import timezone

        profile = make_job_profile(self.org, self.user, self.category, self.level)
        profile.deleted_at = timezone.now()
        profile.save()

        self.assertEqual(JobProfile.objects.filter(id=profile.id).count(), 0)
        self.assertEqual(JobProfile.all_objects.filter(id=profile.id).count(), 1)

    def test_str_representation(self):
        profile = make_job_profile(self.org, self.user, self.category, self.level)
        self.assertIn("Software Engineer", str(profile))
        self.assertIn(self.org.name, str(profile))


class JobProfileAPITests(APITestCase):
    """Test Job Profile API endpoints"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.admin_user = make_user("orgadmin@example.com", "orgadmin")
        self.member_user = make_user("member@example.com", "member")

        self.org = make_approved_org(self.superuser)
        make_member(self.admin_user, self.org, OrganizationMembership.Role.ORG_ADMIN)
        make_member(self.member_user, self.org, OrganizationMembership.Role.MEMBER)

        self.category = JobCategory.objects.create(title="Engineering")
        self.level = ExperienceLevel.objects.create(title="Mid-Level")
        self.profile = make_job_profile(
            self.org, self.admin_user, self.category, self.level
        )

    def test_list_job_profiles_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        url = reverse("list-organization-job-profiles", kwargs={"org_id": self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_job_profiles_requires_membership(self):
        outsider = make_user("outsider@example.com", "outsider")
        self.client.force_authenticate(user=outsider)
        url = reverse("list-organization-job-profiles", kwargs={"org_id": self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_job_profile_is_public(self):
        url = reverse("get-job-profile", kwargs={"job_id": self.profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Software Engineer")

    def test_create_job_profile_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        url = reverse("create-job-profile")
        data = {
            "organization": str(self.org.id),
            "title": "QA Engineer",
            "category": str(self.category.id),
            "experience_level": str(self.level.id),
            "description": "Test QA role.",
            "employment_type": "full_time",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobProfile.objects.count(), 2)

    def test_delete_job_profile_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("delete-job-profile", kwargs={"job_id": self.profile.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobProfile.objects.count(), 0)

    def test_delete_job_profile_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        url = reverse("delete-job-profile", kwargs={"job_id": self.profile.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(JobProfile.objects.count(), 1)
