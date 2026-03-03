from django.db import migrations


def convert_old_statuses(apps, schema_editor):
    """Convert all submitted/under_review applications to to_be_reviewed."""
    JobApplication = apps.get_model("job_applications", "JobApplication")
    JobApplication.objects.filter(status__in=["submitted", "under_review"]).update(
        status="to_be_reviewed"
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "job_applications",
            "0006_change_status_choices_to_be_reviewed_reviewed",
        ),
    ]

    operations = [
        migrations.RunPython(
            convert_old_statuses,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
