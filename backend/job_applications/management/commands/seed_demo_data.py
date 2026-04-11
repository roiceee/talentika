import random
from io import BytesIO

import requests
from django.core.management import call_command
from django.core.management.base import BaseCommand

from job_profile.models import ExperienceLevel, JobCategory, JobProfile, Qualification
from organizations.models import Organization, OrganizationMembership
from users.models import User

from .seed_resume_generator import generate_resume

DEFAULT_BASE_URL = "http://localhost:8000"

FIRST_NAMES = [
    "Juan", "Jose", "Miguel", "Carlos", "Antonio",
    "Eduardo", "Fernando", "Roberto", "Manuel", "Ramon",
    "Maria", "Ana", "Rosa", "Carmen", "Elena",
    "Teresa", "Luz", "Esperanza", "Cristina", "Gloria",
    "Pedro", "Luis", "Ricardo", "Francisco", "Mario",
    "Jorge", "Raul", "Victor", "Arturo", "Alberto",
    "Marilou", "Jennifer", "Michelle", "Andrea", "Kristine",
    "Charisse", "Lovely", "Shiela", "Maricel", "Rowena",
    "Emmanuel", "Patrick", "Gerald", "Dennis", "Ronald",
    "Jomar", "Rodel", "Arvin", "Marlon", "Noel",
]

LAST_NAMES = [
    "Santos", "Reyes", "Cruz", "Bautista", "Ocampo",
    "Garcia", "Mendoza", "Torres", "Castillo", "Dela Cruz",
    "Ramos", "Flores", "Villanueva", "Gonzales", "Aquino",
    "Diaz", "Sy", "Tan", "Lim", "Co",
    "Domingo", "Aguilar", "Salazar", "Navarro", "Morales",
    "Abad", "Bernardo", "Cabrera", "Dela Torre", "Espinosa",
    "Ferrer", "Guevara", "Hernandez", "Ibarra", "Jacinto",
    "Kalaw", "Lazo", "Magno", "Nieto", "Orozco",
    "Padilla", "Quijano", "Rosario", "Soriano", "Tamayo",
    "Umali", "Valdez", "Wagan", "Yap", "Zabala",
]

ORG_USERS = [
    {
        "email": "tester1@example.com",
        "username": "tester1",
        "first_name": "Tester",
        "last_name": "One",
        "password": "password123",
        "role": "ORG_ADMIN",
    },
    {
        "email": "tester2@example.com",
        "username": "tester2",
        "first_name": "Tester",
        "last_name": "Two",
        "password": "password123",
        "role": "MEMBER",
    },
    {
        "email": "tester3@example.com",
        "username": "tester3",
        "first_name": "Tester",
        "last_name": "Three",
        "password": "password123",
        "role": "MEMBER",
    },
]

JOB_PROFILES_DATA = [
    {
        "title": "Accountant III",
        "category": "Finance & Accounting",
        "employment_type": "full_time",
        "experience_level": "Mid-Level (3-5 years)",
        "description": (
            "General Function:\n"
            "Assists the Division Head in supervising the recording and control of all daily financial "
            "transactions and evaluation of all claims and expenses. Assists in supervising the processing "
            "of transactions and the preparation of financial reports.\n\n"
            "Minimum Qualifications:\n"
            "Education: Bachelor's Degree in Commerce or Business Administration, Major in Accounting\n"
            "Experience: 2 years of relevant experience\n"
            "Training: 8 hours of relevant training\n"
            "Eligibility: RA 1080\n\n"
            "Competencies: Financial records management, budget preparation, transaction processing, "
            "systems proficiency, and reporting compliance.\n\n"
            "Application Requirements:\n"
            "Interested and qualified applicants should submit the following documents:\n"
            "- Fully accomplished Personal Data Sheet with recent passport-sized picture\n"
            "- Performance rating in the last rating period (if applicable)\n"
            "- Photocopy of Certificate of Eligibility / Board Rating / License(s)\n"
            "- Photocopy of Transcript of Records\n\n"
            "Applications with incomplete documents will not be entertained."
        ),
        "qualifications": [
            {"category": "education", "name": "Bachelor's Degree in Commerce or Business Administration, Major in Accounting", "requirement_level": "required", "order": 0},
            {"category": "experience", "name": "Relevant accounting or financial management experience", "requirement_level": "required", "years_required": 2, "order": 1},
            {"category": "certification", "name": "RA 1080 (Civil Service Eligibility)", "requirement_level": "required", "order": 2},
            {"category": "other", "name": "8 hours of relevant training", "requirement_level": "required", "order": 3},
            {"category": "skill", "name": "Financial records management", "requirement_level": "required", "order": 4},
            {"category": "skill", "name": "Budget preparation and monitoring", "requirement_level": "required", "order": 5},
            {"category": "skill", "name": "Transaction processing and reporting", "requirement_level": "required", "order": 6},
            {"category": "skill", "name": "Accounting systems proficiency", "requirement_level": "preferred", "order": 7},
        ],
    },
    {
        "title": "Staff Nurse - ICU",
        "category": "Healthcare",
        "employment_type": "full_time",
        "experience_level": "Mid-Level (3-5 years)",
        "description": (
            "Main Functions:\n"
            "The ICU Staff Nurse is responsible for providing comprehensive care to patients who are "
            "experiencing or are at risk for life-threatening conditions. This role requires expertise "
            "in handling emergency and critical care situations.\n\n"
            "Duties and Responsibilities:\n"
            "- Provides patient care as well as education and support to the patient's family\n"
            "- Ensures that life support equipment such as ventilators and feeding tubes function properly\n"
            "- Monitors the patient's heart rate, blood pressure, and respiration for signs of distress\n"
            "- Assesses and closely monitors patients to identify subtle changes in condition "
            "requiring immediate intervention\n"
            "- Interprets, integrates, and responds to a wide array of clinical information\n"
            "- Ensures patients and families are well-informed and involved in care decisions\n\n"
            "Employment Requirements:\n"
            "- Education: Bachelor of Science in Nursing\n"
            "- Licensure: Valid PRC license or permit to practice as a registered nurse\n"
            "- Must be of good moral character\n"
            "- Has extensive experience in the ICU\n"
            "- With Critical Care Training or supporting evidence such as a training certificate "
            "or employment certificate indicating ICU assignment\n\n"
            "Job Type: Full-time\n"
            "Pay: PHP 22,000 \u2013 PHP 23,000 per month\n"
            "Benefits: Opportunities for promotion, paid training, staff meals provided\n"
            "Work Location: In person"
        ),
        "qualifications": [
            {"category": "education", "name": "Bachelor of Science in Nursing", "requirement_level": "required", "order": 0},
            {"category": "certification", "name": "PRC License as Registered Nurse", "requirement_level": "required", "order": 1},
            {"category": "certification", "name": "Critical Care Nursing Training Certificate", "requirement_level": "preferred", "order": 2},
            {"category": "experience", "name": "ICU or critical care nursing experience", "requirement_level": "required", "order": 3},
            {"category": "skill", "name": "Patient care and bedside assessment", "requirement_level": "required", "order": 4},
            {"category": "skill", "name": "Life support equipment operation (ventilators, feeding tubes)", "requirement_level": "required", "order": 5},
            {"category": "skill", "name": "Vital signs monitoring and interpretation", "requirement_level": "required", "order": 6},
            {"category": "skill", "name": "Clinical documentation", "requirement_level": "required", "order": 7},
        ],
    },
    {
        "title": "Barista",
        "category": "Operations",
        "employment_type": "full_time",
        "experience_level": "Mid-Level (3-5 years)",
        "description": (
            "We are looking for a skilled and customer-focused Barista with at least 1 year of experience "
            "in beverage preparation and caf\u00e9 operations. The ideal candidate is creative, friendly, "
            "and passionate about delivering an exceptional coffee experience.\n\n"
            "Key Responsibilities:\n"
            "- Prepare and serve coffee, tea, and specialty beverages according to company standards\n"
            "- Provide excellent customer service and recommend drinks based on customer preferences\n"
            "- Maintain cleanliness of the bar area, equipment, and dining space\n"
            "- Manage inventory of ingredients and supplies; ensure freshness and availability\n"
            "- Assist in cash handling, order taking, and maintaining accurate sales records\n"
            "- Support caf\u00e9 promotions, events, and product displays\n\n"
            "Requirements:\n"
            "- At least 1 year of experience as a barista (Required)\n\n"
            "Job Type: Full-time, Permanent\n"
            "Pay: PHP 14,500 \u2013 PHP 18,000 per month\n"
            "Benefits: Paid training\n"
            "Work Location: In person"
        ),
        "qualifications": [
            {"category": "experience", "name": "Barista or café operations experience", "requirement_level": "required", "years_required": 1, "order": 0},
            {"category": "skill", "name": "Coffee and specialty beverage preparation", "requirement_level": "required", "order": 1},
            {"category": "skill", "name": "Customer service and product recommendation", "requirement_level": "required", "order": 2},
            {"category": "skill", "name": "Bar area and equipment sanitation", "requirement_level": "required", "order": 3},
            {"category": "skill", "name": "Cash handling and order taking", "requirement_level": "preferred", "order": 4},
            {"category": "skill", "name": "Inventory management", "requirement_level": "preferred", "order": 5},
        ],
    },
]

APPLICANTS_PER_PROFILE = 30


class Command(BaseCommand):
    help = (
        "Seed demo data: organization 'test', 3 users, 3 job profiles, "
        f"{APPLICANTS_PER_PROFILE} applicants each."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help=f"Base URL of the running Talentika server (default: {DEFAULT_BASE_URL})",
        )

    def handle(self, *args, **kwargs):
        base_url = kwargs["base_url"].rstrip("/")
        self.stdout.write(self.style.WARNING("Seeding prerequisite job data..."))
        call_command("seed_job_data", verbosity=0)

        rng = random.Random(42)

        self._seed_superuser()
        superuser = User.objects.get(email="superadmin@example.com")

        user_instances = self._seed_org_users()
        org = self._seed_organization(superuser)
        self._seed_memberships(org, user_instances)

        admin_user = user_instances["tester1@example.com"]

        self._seed_job_profiles(org, admin_user, rng, base_url)

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeding complete!"))

    # ------------------------------------------------------------------ #

    def _seed_superuser(self):
        superuser, created = User.objects.get_or_create(
            email="superadmin@example.com",
            defaults={
                "username": "superadmin",
                "first_name": "Super",
                "last_name": "Admin",
                "is_superuser": True,
                "is_staff": True,
            },
        )
        if created:
            superuser.set_password("password123")
            superuser.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Created superuser: superadmin@example.com"))
        else:
            self.stdout.write("  – Superuser already exists")

    def _seed_org_users(self):
        user_instances = {}
        for data in ORG_USERS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                },
            )
            if created:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created user: {data['email']}"))
            else:
                self.stdout.write(f"  – User already exists: {data['email']}")
            user_instances[data["email"]] = user
        return user_instances

    def _seed_organization(self, superuser):
        org, created = Organization.objects.get_or_create(name="test")
        if created:
            org.approve(superuser)
            self.stdout.write(self.style.SUCCESS("  ✓ Created and approved organization: test"))
        else:
            self.stdout.write("  – Organization 'test' already exists")
        return org

    def _seed_memberships(self, org, user_instances):
        for data in ORG_USERS:
            user = user_instances[data["email"]]
            role = (
                OrganizationMembership.Role.ORG_ADMIN
                if data["role"] == "ORG_ADMIN"
                else OrganizationMembership.Role.MEMBER
            )
            _, created = OrganizationMembership.objects.get_or_create(
                user=user,
                organization=org,
                defaults={"role": role},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Added {data['email']} as {data['role']}")
                )
            else:
                self.stdout.write(f"  – Membership already exists: {data['email']}")

    def _seed_job_profiles(self, org, admin_user, rng, base_url):
        for profile_idx, data in enumerate(JOB_PROFILES_DATA, start=1):
            category = JobCategory.objects.get(title=data["category"], organization=None)
            experience_level = ExperienceLevel.objects.get(
                title=data["experience_level"], organization=None
            )

            profile, created = JobProfile.objects.get_or_create(
                title=data["title"],
                organization=org,
                defaults={
                    "created_by": admin_user,
                    "category": category,
                    "employment_type": data["employment_type"],
                    "experience_level": experience_level,
                    "description": data["description"],
                },
            )
            status = "✓ Created" if created else "– Already exists"
            self.stdout.write(
                (self.style.SUCCESS if created else str)(
                    f"  {status}: job profile '{data['title']}'"
                )
            )

            if created:
                self._seed_qualifications(profile, data["qualifications"])

            self._seed_applicants(profile, profile_idx, rng, base_url)

    def _seed_qualifications(self, profile, qualifications):
        for q in qualifications:
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
                f"    ✓ Created {len(qualifications)} qualifications for '{profile.title}'"
            )
        )

    def _seed_applicants(self, profile, profile_idx, rng, base_url):
        from job_applications.models import JobApplication

        existing = JobApplication.objects.filter(job_profile=profile).count()
        to_create = max(0, APPLICANTS_PER_PROFILE - existing)

        if to_create == 0:
            self.stdout.write(
                f"    – Already has {APPLICANTS_PER_PROFILE}+ applicants for '{profile.title}'"
            )
            return

        upload_url = f"{base_url}/api/applications/submit/upload/resume/"
        submit_url = f"{base_url}/api/applications/submit/"
        failed = 0

        for i in range(1, to_create + 1):
            applicant_num = existing + i
            first_name = rng.choice(FIRST_NAMES)
            last_name = rng.choice(LAST_NAMES)
            email = f"applicant_p{profile_idx}_{applicant_num:02d}@example.com"
            phone = f"09{rng.randint(100_000_000, 999_999_999)}"
            filename = f"{first_name.lower()}_{last_name.lower()}_resume.pdf"

            pdf_bytes = generate_resume(
                first_name, last_name, email, phone, profile.title, applicant_num
            )

            # Step 1 — upload resume
            try:
                upload_resp = requests.post(
                    upload_url,
                    files={"file": (filename, BytesIO(pdf_bytes), "application/pdf")},
                    timeout=30,
                )
                upload_resp.raise_for_status()
            except requests.RequestException as exc:
                self.stderr.write(f"    ✗ Upload failed for {email}: {exc}")
                failed += 1
                continue

            file_id = upload_resp.json()["file_id"]

            # Step 2 — submit application
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
                self.stderr.write(f"    ✗ Submit failed for {email}: {exc}")
                failed += 1

        created = to_create - failed
        self.stdout.write(
            self.style.SUCCESS(
                f"    ✓ Submitted {created}/{to_create} applications for '{profile.title}'"
                + (f" ({failed} failed)" if failed else "")
            )
        )
