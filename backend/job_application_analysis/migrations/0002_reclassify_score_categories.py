"""
Data migration: reclassify score categories.

Score categories are computed dynamically from the integer `score` field
(0–100) via `score_categories.py` — no category string is stored in the
database.  The new three-tier classification replaces the old four-tier one:

  Old (four-tier)          New (three-tier)
  ───────────────────────  ──────────────────────────────
  Excellent  (90–100)   →  Suitable            (70–100)
  Good       (75–89)    →  Suitable            (70–100)
  Moderate   (40–74)    →  Potentially Suitable (40–69)
  Bad        (0–39)     →  Unsuitable           (0–39)

Because the category is derived at serialisation time, no row-level UPDATE
is required; the new labels take effect automatically once `score_categories.py`
is updated.  This migration records the reclassification in Django's migration
history.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("job_application_analysis", "0001_initial"),
    ]

    operations = []
