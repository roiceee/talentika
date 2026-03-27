"""
Step 3 of 3: Remove the numeric score field now that score_category is populated.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("job_application_analysis", "0004_backfill_score_category"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="applicationanalysis",
            name="score",
        ),
    ]
