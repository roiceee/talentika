"""
Step 2 of 3: Backfill score_category from existing numeric score values.

Conversion rules (mirrors the final three-tier classification):
  score >= 70  →  suitable
  score >= 40  →  potentially_suitable
  score  < 40  →  unsuitable

Only rows that have a non-null score AND a DONE status are converted.
Rows without a score (analysis not yet complete or failed) are left NULL.
"""

from django.db import migrations


def backfill_score_category(apps, schema_editor):
    ApplicationAnalysis = apps.get_model("job_application_analysis", "ApplicationAnalysis")

    def _to_category(score: int) -> str:
        if score >= 70:
            return "suitable"
        if score >= 40:
            return "potentially_suitable"
        return "unsuitable"

    to_update = []
    for obj in ApplicationAnalysis.objects.filter(
        score__isnull=False,
        status="done",
    ).only("id", "score", "score_category"):
        obj.score_category = _to_category(obj.score)
        to_update.append(obj)

    if to_update:
        ApplicationAnalysis.objects.bulk_update(to_update, ["score_category"])


def reverse_backfill(apps, schema_editor):
    # Clearing score_category is safe — score still exists at this point.
    ApplicationAnalysis = apps.get_model("job_application_analysis", "ApplicationAnalysis")
    ApplicationAnalysis.objects.update(score_category=None)


class Migration(migrations.Migration):

    dependencies = [
        ("job_application_analysis", "0003_add_score_category_field"),
    ]

    operations = [
        migrations.RunPython(backfill_score_category, reverse_code=reverse_backfill),
    ]
