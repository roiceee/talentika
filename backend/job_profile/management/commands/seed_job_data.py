from django.core.management.base import BaseCommand
from job_profile.models import JobCategory, ExperienceLevel, AIScreeningConfiguration


class Command(BaseCommand):
    help = "Seed job categories, experience levels, and AI screening configurations"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Seeding job profile data..."))

        # Seed Job Categories
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
            category, created = JobCategory.objects.get_or_create(title=category_title)
            if created:
                category_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created category: {category_title}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nCreated {category_count} job categories")
        )

        # Seed Experience Levels
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
            level, created = ExperienceLevel.objects.get_or_create(title=level_title)
            if created:
                experience_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created experience level: {level_title}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nCreated {experience_count} experience levels")
        )

        # Seed AI Screening Configurations
        ai_configs = [
            {
                "title": "Strict",
                "description": "Exact Matches Only",
            },
            {
                "title": "Balanced",
                "description": "Allow Similar Skills",
            },
            {
                "title": "Flexible",
                "description": "Consider Potential",
            },
        ]

        ai_config_count = 0
        for config_data in ai_configs:
            config, created = AIScreeningConfiguration.objects.get_or_create(
                title=config_data["title"],
                defaults={"description": config_data["description"]},
            )
            if created:
                ai_config_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created AI config: {config_data['title']}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCreated {ai_config_count} AI screening configurations"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seeding complete! Total: {category_count + experience_count + ai_config_count} records"
            )
        )
