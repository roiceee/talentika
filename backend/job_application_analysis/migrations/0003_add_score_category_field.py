"""
Step 1 of 3: Add the score_category field while keeping score.

The field is nullable so existing rows are unaffected until the backfill
migration (0004) runs.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job_application_analysis", "0002_reclassify_score_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationanalysis",
            name="score_category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("suitable", "Suitable"),
                    ("potentially_suitable", "Potentially Suitable"),
                    ("unsuitable", "Unsuitable"),
                ],
                help_text="AI-assigned candidate-job-fit category",
                max_length=30,
                null=True,
            ),
        ),
    ]
