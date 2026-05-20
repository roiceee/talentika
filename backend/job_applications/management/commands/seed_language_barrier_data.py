"""
Seed a dedicated 'Barista (Language Barrier Test)' job profile in the 'test'
organization with 9 applicants — 3 English + 3 Taglish + 3 Tagalog, each set
covering suitable / potential / unsuitable tiers.

Prerequisites: ensure the backend is running so the OCR→AI pipeline can
process the submitted applications. The command will create the 'test' org
and reuse the tester1 admin if seed_demo_data has been run; otherwise it
creates them on the fly.

Usage:
    uv run python manage.py seed_language_barrier_data
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

from .seed_resume_generator import RESUME_TEMPLATES, build_resume_pdf


def _suitable_english_template():
    """Tier-3 Barista template with the summary updated from '2 years' to
    '3 years' so it matches the new 3-year JD requirement."""
    base = RESUME_TEMPLATES["Barista"][3]
    return {
        **base,
        "summary": base["summary"].replace(
            "2 years of specialty coffee experience",
            "3 years of specialty coffee experience",
        ),
    }


def _potential_english_template():
    """Tier-2 Barista template with experience bumped to 2.5 years (still
    below the 3-year requirement, so 'potentially suitable')."""
    base = RESUME_TEMPLATES["Barista"][2]
    return {
        **base,
        "summary": base["summary"].replace(
            "1 year of experience in espresso preparation",
            "2.5 years of experience in espresso preparation",
        ),
        "experience": [
            {**exp, "period": exp["period"].replace("February 2023", "November 2023")}
            for exp in base["experience"]
        ],
    }

DEFAULT_BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000")

ORG_NAME = "test"
JOB_TITLE = "Barista (Language Barrier Test)"
JOB_CATEGORY = "Operations"
JOB_EXPERIENCE_LEVEL = "Mid-Level (3-5 years)"
JOB_EMPLOYMENT_TYPE = "full_time"

ADMIN_EMAIL = "tester1@example.com"
SUPERUSER_EMAIL = "superadmin@example.com"


# ─────────────────────────────────────────────────────────────────────────────
# Job profile content — mirrors the Barista profile in seed_demo_data so the
# AI judges Taglish/Tagalog résumés against identical qualification criteria.
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# English templates — reuse the existing Barista templates from
# seed_resume_generator so all three language variants describe parallel
# candidates and the AI is comparing apples to apples.
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_TEMPLATES = {
    "suitable":   _suitable_english_template(),
    "potential":  _potential_english_template(),
    "unsuitable": RESUME_TEMPLATES["Barista"][0],
}


# ─────────────────────────────────────────────────────────────────────────────
# Taglish templates (Tagalog + English mix, typical Filipino office tone)
# ─────────────────────────────────────────────────────────────────────────────

TAGLISH_TEMPLATES = {
    "suitable": {
        "summary": (
            "Experienced barista na may 3 years experience sa specialty coffee at "
            "may background sa Hospitality Management. Bihasa sa manual brewing, "
            "espresso dialing, at customer engagement. May experience din mag-train "
            "ng bagong café staff sa beverage standards at service etiquette."
        ),
        "education": [
            {
                "degree": "Bachelor of Science in Hospitality Management",
                "school": "Holy Cross of Davao College",
                "year": "2022",
            },
        ],
        "experience": [
            {
                "title": "Barista / Shift Supervisor",
                "company": "Bo's Coffee – SM Lanang Premier",
                "period": "Hulyo 2022 – Kasalukuyan",
                "duties": [
                    "Nag-prepare ng espresso-based, cold brew, at manual pour-over beverages",
                    "Nag-supervise ng shift team na may 3 baristas at nag-maintain ng service quality standards",
                    "Nag-calibrate ng espresso machines at gumawa ng weekly deep cleaning ng equipment",
                    "In-charge sa daily ingredient inventory at coordination ng supply restocking",
                    "Nag-train ng 2 bagong baristas sa techniques at customer service etiquette",
                ],
            }
        ],
        "skills": [
            "Espresso Dialing",
            "Manual Brewing (Pour-Over, AeroPress, Chemex)",
            "Latte Art",
            "Shift Supervision",
            "Pag-train ng Staff",
            "Inventory Management",
        ],
        "certifications": [
            "SCAE Introduction to Coffee Certificate",
            "Barista Level 1 – Specialty Coffee Association (SCA)",
        ],
    },
    "potential": {
        "summary": (
            "Barista na may 2.5 years experience sa espresso preparation at café "
            "operations. May alam sa standard coffee drinks at basic latte art. "
            "Passionate sa pag-deliver ng quality coffee experience sa bawat customer."
        ),
        "education": [
            {
                "degree": "Bachelor of Science in Hospitality Management (2nd Year, ongoing)",
                "school": "University of Mindanao",
                "year": "Expected 2026",
            },
        ],
        "experience": [
            {
                "title": "Barista",
                "company": "Figaro Coffee Company – Davao",
                "period": "Nobyembre 2023 – Kasalukuyan",
                "duties": [
                    "Nag-prepare ng espresso, drip, at blended coffee beverages base sa standard recipes",
                    "Nagbibigay ng product recommendations base sa taste preferences ng customer",
                    "Gumagamit at naglilinis araw-araw ng espresso machines at grinders",
                    "Tumutulong mag-monitor ng coffee beans at syrup inventory levels",
                ],
            }
        ],
        "skills": [
            "Espresso Preparation",
            "Latte Art (Basic)",
            "Customer Service",
            "POS System",
            "Inventory Tracking",
        ],
        "certifications": [
            "Barista Training Certificate – Figaro Academy (16 hours)",
        ],
    },
    "unsuitable": {
        "summary": (
            "Reliable at hardworking retail professional na may 1 year cashier "
            "experience. Naghahanap ng opportunity para lumago sa customer-facing "
            "service role. Wala pang barista o coffee preparation experience."
        ),
        "education": [
            {
                "degree": "Senior High School Graduate (ABM Strand)",
                "school": "Davao City National High School",
                "year": "2022",
            },
        ],
        "experience": [
            {
                "title": "Cashier",
                "company": "Gaisano Mall – Davao",
                "period": "Abril 2023 – Kasalukuyan",
                "duties": [
                    "Nag-process ng customer purchases at humawak ng cash at digital payments",
                    "Nag-maintain ng accurate transaction records at end-of-day cash counts",
                    "Tumutulong sa stock replenishment at merchandise display sa floor",
                ],
            }
        ],
        "skills": [
            "Cash Handling",
            "Customer Service",
            "POS System",
            "Inventory Counting",
        ],
        "certifications": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Tagalog templates (mostly pure Tagalog; proper nouns + certifications stay
# in English as is typical in real Filipino résumés)
# ─────────────────────────────────────────────────────────────────────────────

TAGALOG_TEMPLATES = {
    "suitable": {
        "summary": (
            "Bihasang tagatimpla ng kape na may tatlong taong karanasan sa "
            "espesyal na kape at may pinag-aralan sa Pamamahala ng Pagtanggap. "
            "Sanay sa manu-manong pagtitimpla, pag-aayos ng espresso, at "
            "pakikipag-ugnayan sa mga mamimili. May karanasan ding magsanay ng "
            "mga bagong tauhan sa pamantayan ng serbisyo at paghahanda ng inumin."
        ),
        "education": [
            {
                "degree": "Batsilyer ng Agham sa Pamamahala ng Pagtanggap",
                "school": "Holy Cross of Davao College",
                "year": "2022",
            },
        ],
        "experience": [
            {
                "title": "Tagatimpla ng Kape / Tagapamahala ng Iskedyul",
                "company": "Bo's Coffee – SM Lanang Premier",
                "period": "Hulyo 2022 – Kasalukuyan",
                "duties": [
                    "Naghahanda ng lahat ng inuming may espresso, malamig na timpla, at manu-manong pour-over",
                    "Namamahala ng pangkat ng tatlong tagatimpla at nagpapanatili ng kalidad ng serbisyo",
                    "Nag-aayos at lingguhang naglilinis ng mga makinang pang-espresso",
                    "Nangangasiwa ng pang-araw-araw na imbentaryo ng sangkap at koordinasyon sa supply",
                    "Nagsanay ng dalawang bagong tagatimpla sa teknik at wastong pakikitungo sa mamimili",
                ],
            }
        ],
        "skills": [
            "Pag-aayos ng Espresso",
            "Manu-manong Pagtitimpla (Pour-Over, AeroPress, Chemex)",
            "Sining ng Latte",
            "Pamamahala ng Iskedyul",
            "Pagsasanay ng Tauhan",
            "Pamamahala ng Imbentaryo",
        ],
        "certifications": [
            "SCAE Introduction to Coffee Certificate",
            "Barista Level 1 – Specialty Coffee Association (SCA)",
        ],
    },
    "potential": {
        "summary": (
            "Tagatimpla ng kape na may dalawa't kalahating taong karanasan sa "
            "paghahanda ng espresso at pagpapatakbo ng kapehan. May kaalaman sa "
            "karaniwang inuming kape at panimulang sining ng latte. Masugid sa "
            "paghahatid ng dekalidad na karanasan ng kape sa bawat mamimili."
        ),
        "education": [
            {
                "degree": "Batsilyer ng Agham sa Pamamahala ng Pagtanggap (Ikalawang Taon, kasalukuyang nag-aaral)",
                "school": "University of Mindanao",
                "year": "Inaasahang 2026",
            },
        ],
        "experience": [
            {
                "title": "Tagatimpla ng Kape",
                "company": "Figaro Coffee Company – Davao",
                "period": "Nobyembre 2023 – Kasalukuyan",
                "duties": [
                    "Naghahanda ng espresso, drip, at pinaghalong inuming kape ayon sa pamantayang resipi",
                    "Nagbibigay ng rekomendasyon ng produkto base sa panlasa ng mamimili",
                    "Pinapatakbo at araw-araw na nililinis ang mga makinang pang-espresso at giling",
                    "Tumutulong magbantay sa antas ng imbentaryo ng butil ng kape at sirap",
                ],
            }
        ],
        "skills": [
            "Paghahanda ng Espresso",
            "Sining ng Latte (Panimula)",
            "Serbisyo sa Mamimili",
            "Sistema ng POS",
            "Pagsubaybay sa Imbentaryo",
        ],
        "certifications": [
            "Barista Training Certificate – Figaro Academy (16 oras)",
        ],
    },
    "unsuitable": {
        "summary": (
            "Maaasahan at masipag na manggagawa sa tindahan na may isang taong "
            "karanasan bilang kahera. Naghahanap ng pagkakataong umunlad sa "
            "tungkulin na nakikipag-ugnayan sa mga mamimili. Wala pang karanasan "
            "bilang tagatimpla o sa paghahanda ng kape."
        ),
        "education": [
            {
                "degree": "Nagtapos sa Senior High School (ABM Strand)",
                "school": "Davao City National High School",
                "year": "2022",
            },
        ],
        "experience": [
            {
                "title": "Kahera",
                "company": "Gaisano Mall – Davao",
                "period": "Abril 2023 – Kasalukuyan",
                "duties": [
                    "Nag-proseso ng mga binili ng mamimili at humawak ng pera at digital na bayad",
                    "Nagpapanatili ng tumpak na talaan ng transaksyon at pagbilang ng pera sa katapusan ng araw",
                    "Tumutulong sa muling pagpupuno ng paninda at pag-aayos ng display",
                ],
            }
        ],
        "skills": [
            "Paghawak ng Pera",
            "Serbisyo sa Mamimili",
            "Sistema ng POS",
            "Pagbilang ng Imbentaryo",
        ],
        "certifications": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Applicant identity per (language, tier). Fixed values so reseed is
# idempotent on email/phone uniqueness and easy to spot in the dashboard.
# ─────────────────────────────────────────────────────────────────────────────

APPLICANTS = [
    # (language, tier, first_name, last_name, email_local, phone, style_idx)
    # Suitable persona — last name shared across language variants
    ("english", "suitable",   "Patricia", "Mendoza",    "applicant01", "09170001001", 0),
    ("taglish", "suitable",   "Marielle", "Mendoza",    "applicant02", "09170001002", 1),
    ("tagalog", "suitable",   "Reynalda", "Mendoza",    "applicant03", "09170001003", 2),
    # Potential persona — last name shared across language variants
    ("english", "potential",  "Mark",     "Villanueva", "applicant04", "09170001004", 3),
    ("taglish", "potential",  "Joshua",   "Villanueva", "applicant05", "09170001005", 4),
    ("tagalog", "potential",  "Carlito",  "Villanueva", "applicant06", "09170001006", 0),
    # Unsuitable persona — last name shared across language variants
    ("english", "unsuitable", "Karen",    "Aquino",     "applicant07", "09170001007", 1),
    ("taglish", "unsuitable", "Jasmine",  "Aquino",     "applicant08", "09170001008", 2),
    ("tagalog", "unsuitable", "Bituin",   "Aquino",     "applicant09", "09170001009", 3),
]

TEMPLATE_SETS = {
    "english": ENGLISH_TEMPLATES,
    "taglish": TAGLISH_TEMPLATES,
    "tagalog": TAGALOG_TEMPLATES,
}


class Command(BaseCommand):
    help = (
        "Seed a dedicated 'Barista (Language Barrier Test)' job profile in the "
        "'test' organization with 9 applicants (3 English + 3 Taglish + 3 "
        "Tagalog, each covering suitable / potential / unsuitable tiers)."
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
                f"\nSeeding language-barrier applicants for '{profile.title}' in '{org.name}'..."
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
            defaults={
                "username": "tester1",
                "first_name": "Tester",
                "last_name": "One",
            },
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created admin user: {ADMIN_EMAIL}"))

        OrganizationMembership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={"role": OrganizationMembership.Role.ORG_ADMIN},
        )
        return user

    def _get_or_create_job_profile(self, org, admin_user):
        category = JobCategory.objects.get(title=JOB_CATEGORY, organization=None)
        experience_level = ExperienceLevel.objects.get(
            title=JOB_EXPERIENCE_LEVEL, organization=None
        )

        profile, created = JobProfile.objects.get_or_create(
            title=JOB_TITLE,
            organization=org,
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

        for language, tier, first_name, last_name, email_local, phone, style_idx in APPLICANTS:
            email = f"{email_local}@example.com"
            template = TEMPLATE_SETS[language][tier]
            safe_last = last_name.lower().replace(" ", "_")
            filename = f"{first_name.lower()}_{safe_last}_resume.pdf"

            pdf_bytes = build_resume_pdf(
                first_name, last_name, email, phone, template, style_idx
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
                    f"  ✓ Submitted [{language:7s} / {tier:10s}] {first_name} {last_name} <{email}>"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Language-barrier seeding complete: "
                f"{submitted} submitted, {failed} failed."
            )
        )
