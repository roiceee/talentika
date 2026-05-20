"""
Seed a dedicated 'Barista (OCR Robustness Test)' job profile in the 'test'
organization with 5 applicants whose résumés use heavily graphical layouts
(photo banners, sidebars, color-block headers, timeline infographics,
magazine-style two-column). All five applicants carry identical factual
content (the suitable Barista persona), so any variation in AI scoring
between them is attributable to the OCR layer, not to differences in
qualifications.

Usage:
    uv run python manage.py seed_ocr_test_data
"""

import os
from io import BytesIO

import requests
from django.core.management import call_command
from django.core.management.base import BaseCommand

from job_profile.models import (
    ExperienceLevel,
    JobCategory,
    JobProfile,
    Qualification,
)
from organizations.models import Organization, OrganizationMembership
from users.models import User

from .seed_graphical_resume_generator import (
    GRAPHICAL_STYLE_NAMES,
    build_graphical_resume,
)
from .seed_resume_generator import RESUME_TEMPLATES

DEFAULT_BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000")

ORG_NAME = "test"
JOB_TITLE = "Barista (OCR Robustness Test)"
JOB_CATEGORY = "Operations"
JOB_EXPERIENCE_LEVEL = "Mid-Level (3-5 years)"
JOB_EMPLOYMENT_TYPE = "full_time"

ADMIN_EMAIL = "tester1@example.com"
SUPERUSER_EMAIL = "superadmin@example.com"


JOB_DESCRIPTION = (
    "We are looking for a skilled and customer-focused Barista with at least 3 years of experience "
    "in beverage preparation and café operations. The ideal candidate is creative, friendly, "
    "and passionate about delivering an exceptional coffee experience.\n\n"
    "Key Responsibilities:\n"
    "- Prepare and serve coffee, tea, and specialty beverages according to company standards\n"
    "- Provide excellent customer service and recommend drinks based on customer preferences\n"
    "- Maintain cleanliness of the bar area, equipment, and dining space\n"
    "- Manage inventory of ingredients and supplies; ensure freshness and availability\n"
    "- Assist in cash handling, order taking, and maintaining accurate sales records\n"
    "- Support café promotions, events, and product displays\n\n"
    "Requirements:\n"
    "- At least 3 years of experience as a barista (Required)\n\n"
    "Job Type: Full-time, Permanent\n"
    "Pay: PHP 14,500 – PHP 18,000 per month\n"
    "Benefits: Paid training\n"
    "Work Location: In person"
)

JOB_QUALIFICATIONS = [
    {"category": "experience", "name": "Barista or café operations experience", "requirement_level": "required", "years_required": 3, "order": 0},
    {"category": "skill", "name": "Coffee and specialty beverage preparation", "requirement_level": "required", "order": 1},
    {"category": "skill", "name": "Customer service and product recommendation", "requirement_level": "required", "order": 2},
    {"category": "skill", "name": "Bar area and equipment sanitation", "requirement_level": "required", "order": 3},
    {"category": "skill", "name": "Cash handling and order taking", "requirement_level": "preferred", "order": 4},
    {"category": "skill", "name": "Inventory management", "requirement_level": "preferred", "order": 5},
]


# All five applicants share this résumé content (tier-3 Barista, "suitable"),
# bumped to 3 years and with cash handling added so the candidate is a clean
# match for the JD. Only the visual style varies.
def _suitable_template():
    base = RESUME_TEMPLATES["Barista"][3]
    extra_duty = (
        "Handled daily cash and card transactions, took customer orders at "
        "the POS, and reconciled end-of-shift sales reports"
    )
    return {
        **base,
        "summary": base["summary"].replace(
            "2 years of specialty coffee experience",
            "3 years of specialty coffee experience",
        ),
        "experience": [
            {**exp, "duties": [*exp["duties"], extra_duty]}
            for exp in base["experience"]
        ],
        "skills": [*base["skills"], "Cash Handling & POS Operations", "Order Taking"],
    }


SUITABLE_TEMPLATE = _suitable_template()


# Five distinct identities so each style attaches to its own applicant card
# in the dashboard, while none of them duplicate against each other.
SHARED_LAST_NAME = "Santos"

APPLICANTS = [
    # (style_idx, first_name, last_name, email_local, phone)
    (0, "Photo Banner",    SHARED_LAST_NAME, "ocr01", "09180001001"),
    (1, "Dark Sidebar",    SHARED_LAST_NAME, "ocr02", "09180001002"),
    (2, "Color Blocks",    SHARED_LAST_NAME, "ocr03", "09180001003"),
    (3, "Timeline Peach",  SHARED_LAST_NAME, "ocr04", "09180001004"),
    (4, "Yellow Sidebar",  SHARED_LAST_NAME, "ocr05", "09180001005"),
]


class Command(BaseCommand):
    help = (
        "Seed a 'Barista (OCR Robustness Test)' job profile in the 'test' "
        "organization with 5 heavily graphical résumés (photo banner, dark "
        "sidebar, color blocks, timeline infographic, magazine layout)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help=f"Base URL of the running Talentika server (default: {DEFAULT_BASE_URL})",
        )

    def handle(self, *args, **kwargs):
        base_url = kwargs["base_url"].rstrip("/")

        self.stdout.write(self.style.WARNING("Ensuring prerequisite job data..."))
        call_command("seed_job_data", verbosity=0)

        org = self._get_or_create_organization()
        admin_user = self._get_or_create_admin(org)
        profile = self._get_or_create_job_profile(org, admin_user)

        self.stdout.write(
            self.style.WARNING(
                f"\nSeeding graphical OCR-test applicants for '{profile.title}' in '{org.name}'..."
            )
        )
        self._submit_applicants(profile, base_url)

    # ------------------------------------------------------------------ #

    def _get_or_create_organization(self):
        org, created = Organization.objects.get_or_create(name=ORG_NAME)
        if created:
            superuser, _ = User.objects.get_or_create(
                email=SUPERUSER_EMAIL,
                defaults={
                    "username": "superadmin",
                    "first_name": "Super",
                    "last_name": "Admin",
                    "is_superuser": True,
                    "is_staff": True,
                },
            )
            if not superuser.has_usable_password():
                superuser.set_password("password123")
                superuser.save()
            org.approve(superuser)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created organization: {ORG_NAME}"))
        else:
            self.stdout.write(f"  – Organization '{ORG_NAME}' already exists")
        return org

    def _get_or_create_admin(self, org):
        user, created = User.objects.get_or_create(
            email=ADMIN_EMAIL,
            defaults={"username": "tester1", "first_name": "Tester", "last_name": "One"},
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created admin user: {ADMIN_EMAIL}"))
        OrganizationMembership.objects.get_or_create(
            user=user, organization=org,
            defaults={"role": OrganizationMembership.Role.ORG_ADMIN},
        )
        return user

    def _get_or_create_job_profile(self, org, admin_user):
        category = JobCategory.objects.get(title=JOB_CATEGORY, organization=None)
        experience_level = ExperienceLevel.objects.get(
            title=JOB_EXPERIENCE_LEVEL, organization=None
        )
        profile, created = JobProfile.objects.get_or_create(
            title=JOB_TITLE, organization=org,
            defaults={
                "created_by": admin_user,
                "category": category,
                "employment_type": JOB_EMPLOYMENT_TYPE,
                "experience_level": experience_level,
                "description": JOB_DESCRIPTION,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created job profile: '{JOB_TITLE}'"))
            for q in JOB_QUALIFICATIONS:
                Qualification.objects.create(
                    job_profile=profile,
                    category=q["category"],
                    name=q["name"],
                    requirement_level=q.get("requirement_level", "required"),
                    years_required=q.get("years_required"),
                    proficiency_level=q.get("proficiency_level"),
                    order=q.get("order", 0),
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Created {len(JOB_QUALIFICATIONS)} qualifications"
                )
            )
        else:
            self.stdout.write(f"  – Job profile '{JOB_TITLE}' already exists")
        return profile

    def _submit_applicants(self, profile, base_url):
        upload_url = f"{base_url}/api/applications/submit/upload/resume/"
        submit_url = f"{base_url}/api/applications/submit/"

        submitted = 0
        failed = 0

        for style_idx, first_name, last_name, email_local, phone in APPLICANTS:
            email = f"{email_local}@example.com"
            style_name = GRAPHICAL_STYLE_NAMES[style_idx]
            safe_last = last_name.lower().replace(" ", "_")
            filename = f"{first_name.lower()}_{safe_last}_resume.pdf"

            pdf_bytes = build_graphical_resume(
                first_name, last_name, email, phone, SUITABLE_TEMPLATE, style_idx
            )

            try:
                upload_resp = requests.post(
                    upload_url,
                    files={"file": (filename, BytesIO(pdf_bytes), "application/pdf")},
                    timeout=30,
                )
                upload_resp.raise_for_status()
            except requests.RequestException as exc:
                body = getattr(exc.response, "text", "")[:500] if getattr(exc, "response", None) is not None else ""
                self.stderr.write(f"    ✗ Upload failed for {email}: {exc}  body={body}")
                failed += 1
                continue

            file_id = upload_resp.json()["file_id"]

            try:
                submit_resp = requests.post(
                    submit_url,
                    json={
                        "job_profile": str(profile.id),
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "address": {
                            "line1": "123 Sample Street",
                            "city": "Davao City",
                            "province_state": "Davao del Sur",
                            "postal_code": "8000",
                            "country": "PH",
                        },
                        "resume_id": file_id,
                        "answers": [],
                    },
                    timeout=30,
                )
                submit_resp.raise_for_status()
            except requests.RequestException as exc:
                body = getattr(exc.response, "text", "")[:500] if getattr(exc, "response", None) is not None else ""
                self.stderr.write(f"    ✗ Submit failed for {email}: {exc}  body={body}")
                failed += 1
                continue

            submitted += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Submitted [{style_name:22s}] {first_name} {last_name} <{email}>"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ OCR-test seeding complete: {submitted} submitted, {failed} failed."
            )
        )
