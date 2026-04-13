"""
Unit tests for Job Applications app.

Tests cover:
- JobApplication model creation, default status, and soft delete
- API: list, get, update status, delete
- Permission checks (admin vs member)
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User
from organizations.models import Organization, OrganizationMembership
from job_profile.models import JobCategory, ExperienceLevel, JobProfile
from job_applications.models import JobApplication


def make_user(email, username):
    return User.objects.create_user(email=email, username=username, password="pass")


def make_approved_org(superuser, name="Test Org"):
    org = Organization.objects.create(name=name)
    org.approve(superuser)
    return org


def make_member(user, org, role=OrganizationMembership.Role.MEMBER):
    OrganizationMembership.objects.create(user=user, organization=org, role=role)


def make_job_profile(org, user):
    category = JobCategory.objects.create(title="Engineering")
    level = ExperienceLevel.objects.create(title="Mid-Level")
    return JobProfile.objects.create(
        organization=org,
        created_by=user,
        title="Software Engineer",
        category=category,
        experience_level=level,
        description="A test role.",
        employment_type=JobProfile.EmploymentType.FULL_TIME,
    )


def make_application(job_profile):
    return JobApplication.objects.create(
        job_profile=job_profile,
        first_name="Juan",
        last_name="dela Cruz",
        email="juan@example.com",
        phone="09171234567",
    )


class JobApplicationModelTests(TestCase):
    """Test JobApplication model behaviour"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.user = make_user("member@example.com", "member")
        self.org = make_approved_org(self.superuser)
        self.profile = make_job_profile(self.org, self.user)

    def test_application_default_status_is_to_be_reviewed(self):
        app = make_application(self.profile)
        self.assertEqual(app.status, JobApplication.Status.TO_BE_REVIEWED)

    def test_soft_delete_hides_from_default_manager(self):
        app = make_application(self.profile)
        app.deleted_at = timezone.now()
        app.save()

        self.assertEqual(JobApplication.objects.filter(id=app.id).count(), 0)
        self.assertEqual(JobApplication.all_objects.filter(id=app.id).count(), 1)

    def test_str_representation(self):
        app = make_application(self.profile)
        self.assertIn("Juan", str(app))
        self.assertIn("Software Engineer", str(app))


class JobApplicationAPITests(APITestCase):
    """Test Job Application API endpoints"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", username="admin", password="pass"
        )
        self.admin_user = make_user("orgadmin@example.com", "orgadmin")
        self.member_user = make_user("member@example.com", "member")

        self.org = make_approved_org(self.superuser)
        make_member(self.admin_user, self.org, OrganizationMembership.Role.ORG_ADMIN)
        make_member(self.member_user, self.org, OrganizationMembership.Role.MEMBER)

        self.job_profile = make_job_profile(self.org, self.admin_user)
        self.application = make_application(self.job_profile)

    def _list_url(self):
        return reverse(
            "list_job_applications",
            kwargs={"org_id": self.org.id, "job_profile_id": self.job_profile.id},
        )

    def _detail_url(self):
        return reverse(
            "get_job_application",
            kwargs={
                "org_id": self.org.id,
                "job_profile_id": self.job_profile.id,
                "job_application_id": self.application.id,
            },
        )

    def _status_url(self):
        return reverse(
            "update_application_status",
            kwargs={
                "org_id": self.org.id,
                "job_profile_id": self.job_profile.id,
                "job_application_id": self.application.id,
            },
        )

    def _delete_url(self):
        return reverse(
            "delete_job_application",
            kwargs={
                "org_id": self.org.id,
                "job_profile_id": self.job_profile.id,
                "job_application_id": self.application.id,
            },
        )

    def test_list_applications_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self._list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_applications_requires_auth(self):
        response = self.client.get(self._list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_application_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self._detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Juan")

    def test_update_status_as_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(
            self._status_url(), {"status": "shortlisted"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.SHORTLISTED)

    def test_update_status_rejects_invalid_value(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(
            self._status_url(), {"status": "invalid_status"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_application_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self._delete_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_delete_application_as_member_forbidden(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self._delete_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(JobApplication.objects.count(), 1)
