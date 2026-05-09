# Synthetic Demo Data — `seed_demo_data`

This command generates a complete set of fabricated data for a test organization, including users, job profiles, and job applications. It is intended for demonstration, pilot testing, and system evaluation purposes.

```bash
uv run python manage.py seed_demo_data
```

### What Gets Created

**Users**

| Email | Role |
|-------|------|
| superadmin@example.com | Superuser |
| tester1@example.com | Org Admin |
| tester2@example.com | Member |
| tester3@example.com | Member |
| tester4@example.com | Member |
| tester5@example.com | Member |

All accounts use the password `password123`.

**Organization**

A single organization named **"test"** is created and approved. All users above are added as members under this organization.

**Job Profiles (5 total)**

Five realistic job profiles are created under the test organization, each with a full set of qualifications:

| Title | Category | Experience Level |
|-------|----------|-----------------|
| Accountant III | Finance & Accounting | Mid-Level (3–5 years) |
| Staff Nurse - ICU | Healthcare | Mid-Level (3–5 years) |
| Barista | Operations | Mid-Level (3–5 years) |
| Clinical Coder | Healthcare | Entry Level (0–2 years) |
| Customer Service Representative | Customer Support | Entry Level (0–2 years) |

The job descriptions and qualifications are based on real Philippine job postings, making them representative of actual hiring scenarios.

**Applications (30 per job profile = 150 total)**

For each job profile, 30 synthetic applicants are generated and submitted. Each applicant is assigned:
- A **randomized Filipino name** drawn from a pool of 50 first names and 50 last names
- A **unique email address** using the `@example.com` domain, which is reserved by IANA for documentation and testing purposes and cannot belong to a real user
- A **phone number** using the `0900` prefix, which is unassigned by any Philippine carrier and therefore cannot correspond to a real subscriber. Numbers are generated deterministically as `0900` + profile index + applicant number, ensuring no collisions across runs

For each applicant, the command:
1. Generates a synthetic PDF resume using a programmatic resume builder
2. Uploads the PDF via the resume upload API
3. Submits the full application via the application submission API

Because submissions go through the actual API endpoints, each application enters the real processing pipeline — OCR extracts the resume text, and the AI analysis worker scores the applicant against the job profile's qualifications. The synthetic data therefore produces real AI-generated analysis results, not placeholder values.

### Idempotency

The command is safe to re-run. Users, the organization, memberships, and job profiles are created with `get_or_create` and skipped if they already exist. For applications, it checks how many already exist per profile and only creates the remainder up to the target of 30.
