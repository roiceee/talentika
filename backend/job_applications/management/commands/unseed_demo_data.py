from django.core.management.base import BaseCommand

from job_profile.models import JobProfile
from organizations.models import Organization
from users.models import User

SEED_EMAILS = [
    "superadmin@example.com",
    "tester1@example.com",
    "tester2@example.com",
    "tester3@example.com",
]

SEED_ORG_NAME = "test"

SEED_JOB_PROFILE_TITLES = [
    "Accountant III",
    "Staff Nurse - ICU",
    "Barista",
    "Clinical Coder",
    "Customer Service Representative",
]


class Command(BaseCommand):
    help = "Delete all data created by seed_demo_data (org, users, job profiles, applicants)."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Removing demo seed data..."))

        self._delete_job_profiles()
        self._delete_organization()
        self._delete_users()

        self.stdout.write(self.style.SUCCESS("\n✅ Demo seed data removed."))

    # ------------------------------------------------------------------ #

    def _delete_job_profiles(self):
        try:
            org = Organization.objects.get(name=SEED_ORG_NAME)
        except Organization.DoesNotExist:
            self.stdout.write("  – Organization 'test' not found, skipping job profiles")
            return

        profiles = JobProfile.all_objects.filter(
            organization=org, title__in=SEED_JOB_PROFILE_TITLES
        )
        count = profiles.count()
        if count:
            # Deleting profiles cascades to Qualification and JobApplication
            # (and their ApplicantAddress / ApplicationAttachment children)
            profiles.delete()
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Deleted {count} job profile(s) and all related data")
            )
        else:
            self.stdout.write("  – No seed job profiles found")

    def _delete_organization(self):
        deleted, _ = Organization.all_objects.filter(name=SEED_ORG_NAME).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted organization '{SEED_ORG_NAME}'"))
        else:
            self.stdout.write(f"  – Organization '{SEED_ORG_NAME}' not found")

    def _delete_users(self):
        deleted, _ = User.all_objects.filter(email__in=SEED_EMAILS).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted {deleted} seed user(s)"))
        else:
            self.stdout.write("  – No seed users found")


