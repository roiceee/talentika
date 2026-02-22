# No-op: User model was consolidated into 0001_initial to fix circular dependency

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = []
