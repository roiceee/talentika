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
                "title": "Standard Technical Screening",
                "description": "AI-powered screening focused on technical skills assessment, coding proficiency, and problem-solving abilities. Evaluates candidates based on technical knowledge and hands-on experience.",
            },
            {
                "title": "Behavioral Assessment",
                "description": "Screening configuration emphasizing soft skills, communication abilities, teamwork, and cultural fit. Uses AI to analyze behavioral patterns and interpersonal skills.",
            },
            {
                "title": "Leadership Evaluation",
                "description": "Advanced screening for leadership positions focusing on strategic thinking, decision-making, team management, and organizational impact.",
            },
            {
                "title": "Entry Level Assessment",
                "description": "Tailored screening for entry-level positions emphasizing learning potential, basic skills, educational background, and enthusiasm.",
            },
            {
                "title": "Comprehensive Screening",
                "description": "Complete assessment combining technical skills, behavioral traits, cultural fit, and experience evaluation for comprehensive candidate analysis.",
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
