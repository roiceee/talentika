"""
Integration tests — Job profile and application flow

Covers the full sequence:
  Org setup → Create job profile → Submit application (public) →
  HR lists and views applications → HR updates status → Admin deletes application
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User
from organizations.models import Organization, OrganizationMembership
from job_profile.models import JobCategory, ExperienceLevel, JobProfile
from job_applications.models import JobApplication, TemporaryFileUpload


def make_approved_org(superuser, admin_user, name="Test Corp"):
    org = Organization.objects.create(name=name)
    org.approve(superuser)
    OrganizationMembership.objects.create(
        user=admin_user, organization=org, role=OrganizationMembership.Role.ORG_ADMIN
    )
    return org


def make_job_profile(org, user):
    category = JobCategory.objects.create(title="Technology")
    level = ExperienceLevel.objects.create(title="Entry Level")
    return JobProfile.objects.create(
        organization=org,
        created_by=user,
        title="Junior Developer",
        category=category,
        experience_level=level,
        description="Entry level dev role.",
        employment_type=JobProfile.EmploymentType.FULL_TIME,
    )


def make_temp_upload():
    """Create a TemporaryFileUpload record directly, bypassing actual file storage."""
    return TemporaryFileUpload.objects.create(
        storage_path="test/resume.pdf",
        file_name="resume.pdf",
        file_size=1024,
        content_type="application/pdf",
        sha256_hash="a" * 64,
    )


class JobApplicationFlowTests(APITestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="super@example.com", username="super", password="pass"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", username="admin", password="pass"
        )
        self.member = User.objects.create_user(
            email="member@example.com", username="member", password="pass"
        )

        self.org = make_approved_org(self.superuser, self.admin)
        OrganizationMembership.objects.create(
            user=self.member,
            organization=self.org,
            role=OrganizationMembership.Role.MEMBER,
        )
        self.job_profile = make_job_profile(self.org, self.admin)

    def test_full_application_flow(self):
        # 1. Submit application as public user (no auth)
        temp = make_temp_upload()
        submit_resp = self.client.post(
            reverse("submit_job_application"),
            {
                "job_profile": str(self.job_profile.id),
                "first_name": "Maria",
                "last_name": "Santos",
                "email": "maria@example.com",
                "phone": "09171234567",
                "resume_id": str(temp.id),
                "address": {
                    "line1": "123 Rizal St",
                    "city": "Davao City",
                    "province_state": "Davao del Sur",
                    "postal_code": "8000",
                    "country": "PH",
                },
                "answers": [],
            },
            format="json",
        )
        self.assertEqual(submit_resp.status_code, status.HTTP_201_CREATED)
        application_id = submit_resp.data["id"]
        self.assertEqual(submit_resp.data["status"], "to_be_reviewed")

        # 2. HR member lists applications and sees the new one
        self.client.force_authenticate(user=self.member)
        list_resp = self.client.get(
            reverse(
                "list_job_applications",
                kwargs={
                    "org_id": self.org.id,
                    "job_profile_id": self.job_profile.id,
                },
            )
        )
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(list_resp.data["count"], 1)

        # 3. HR member views the application detail
        detail_resp = self.client.get(
            reverse(
                "get_job_application",
                kwargs={
                    "org_id": self.org.id,
                    "job_profile_id": self.job_profile.id,
                    "job_application_id": application_id,
                },
            )
        )
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data["first_name"], "Maria")

        # 4. HR member updates application status to shortlisted
        status_resp = self.client.patch(
            reverse(
                "update_application_status",
                kwargs={
                    "org_id": self.org.id,
                    "job_profile_id": self.job_profile.id,
                    "job_application_id": application_id,
                },
            ),
            {"status": "shortlisted"},
            format="json",
        )
        self.assertEqual(status_resp.status_code, status.HTTP_200_OK)

        app = JobApplication.objects.get(id=application_id)
        self.assertEqual(app.status, JobApplication.Status.SHORTLISTED)

        # 5. Admin deletes the application
        self.client.force_authenticate(user=self.admin)
        delete_resp = self.client.delete(
            reverse(
                "delete_job_application",
                kwargs={
                    "org_id": self.org.id,
                    "job_profile_id": self.job_profile.id,
                    "job_application_id": application_id,
                },
            )
        )
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_duplicate_application_rejected(self):
        """Same applicant cannot submit twice for the same job profile."""
        temp1 = make_temp_upload()
        payload = {
            "job_profile": str(self.job_profile.id),
            "first_name": "Juan",
            "last_name": "dela Cruz",
            "email": "juan@example.com",
            "phone": "09181234567",
            "resume_id": str(temp1.id),
            "address": {
                "line1": "1 Test St",
                "city": "Manila",
                "province_state": "Metro Manila",
                "postal_code": "1000",
                "country": "PH",
            },
            "answers": [],
        }
        resp1 = self.client.post(reverse("submit_job_application"), payload, format="json")
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        temp2 = make_temp_upload()
        payload["resume_id"] = str(temp2.id)
        resp2 = self.client.post(reverse("submit_job_application"), payload, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_job_profile_rejects_application(self):
        self.job_profile.is_active = False
        self.job_profile.save()

        temp = make_temp_upload()
        resp = self.client.post(
            reverse("submit_job_application"),
            {
                "job_profile": str(self.job_profile.id),
                "first_name": "Ana",
                "last_name": "Reyes",
                "email": "ana@example.com",
                "phone": "09991234567",
                "resume_id": str(temp.id),
                "address": {
                    "line1": "2 Test Ave",
                    "city": "Cebu City",
                    "province_state": "Cebu",
                    "postal_code": "6000",
                    "country": "PH",
                },
                "answers": [],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
