from django.core.management.base import BaseCommand
from job_profile.models import JobCategory, ExperienceLevel


class Command(BaseCommand):
    help = "Seed job categories and experience levels"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Seeding job profile data..."))

        categories = [
            "Software Engineering",
            "Data Science & Analytics",
            "Product Management",
            "Design (UI/UX)",
            "Marketing",
            "Sales",
            "Human Resources",
            "Finance & Accounting",
            "Operations",
            "Customer Support",
            "Legal",
            "Business Development",
            "Engineering (Non-Software)",
            "Healthcare",
            "Education & Training",
        ]

        category_count = 0
        for category_title in categories:
            _, created = JobCategory.objects.get_or_create(title=category_title)
            if created:
                category_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created category: {category_title}"))
        self.stdout.write(self.style.SUCCESS(f"\nCreated {category_count} job categories"))

        experience_levels = [
            "Internship",
            "Entry Level (0-2 years)",
            "Mid-Level (3-5 years)",
            "Senior Level (6-10 years)",
            "Lead/Principal (10+ years)",
            "Executive/C-Level",
        ]

        experience_count = 0
        for level_title in experience_levels:
            _, created = ExperienceLevel.objects.get_or_create(title=level_title)
            if created:
                experience_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created experience level: {level_title}"))
        self.stdout.write(self.style.SUCCESS(f"\nCreated {experience_count} experience levels"))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Seeding complete! Total: {category_count + experience_count} records"
        ))
