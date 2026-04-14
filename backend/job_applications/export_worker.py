"""
RQ task for generating application export files (CSV / XLSX).

Queue: ``export_queue``

Each task receives an ``export_job_id`` (UUID), queries the relevant
applications + analysis data, writes a file to local storage, and marks
the export job as done.
"""

import csv
import io
import logging
import traceback
from pathlib import Path  # still needed for xlsx temp file

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def enqueue_export(export_job_id: str):
    """Enqueue an export task on ``export_queue``."""
    from rq import Queue
    from job_application_analysis.workers import _get_redis_connection

    q = Queue("export_queue", connection=_get_redis_connection())
    q.enqueue(process_export, export_job_id)
    logger.info("Enqueued export task for job %s", export_job_id)


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

COLUMNS = [
    ("First Name", lambda app, _a: app.first_name),
    ("Last Name", lambda app, _a: app.last_name),
    ("Email", lambda app, _a: app.email),
    ("Phone", lambda app, _a: app.phone),
    ("Status", lambda app, _a: app.get_status_display()),
    (
        "Submitted At",
        lambda app, _a: app.submitted_at.isoformat() if app.submitted_at else "",
    ),
    # Address
    ("City", lambda app, _a: getattr(getattr(app, "_address_cache", None), "city", "")),
    (
        "Country",
        lambda app, _a: getattr(getattr(app, "_address_cache", None), "country", ""),
    ),
    # Analysis
    ("Analysis Status", lambda _app, a: a.get_status_display() if a else ""),
    ("Score Category", lambda _app, a: _score_cat_label(a)),
    ("AI Summary", lambda _app, a: a.ai_analysis_summary if a else ""),
    (
        "Key Skills",
        lambda _app, a: ", ".join(a.key_skills) if a and a.key_skills else "",
    ),
    (
        "Notable Traits",
        lambda _app, a: ", ".join(a.notable_traits) if a and a.notable_traits else "",
    ),
]


def _score_cat_label(analysis):
    if not analysis or not analysis.score_category:
        return ""
    from job_application_analysis.score_categories import get_score_category

    cat = get_score_category(analysis.score_category)
    return cat.label if cat else ""


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


def process_export(export_job_id: str):
    """Generate the export file for the given ApplicationExportJob."""
    from job_applications.models import ApplicationExportJob, JobApplication
    from job_application_analysis.models import ApplicationAnalysis

    export_job = ApplicationExportJob.objects.select_related("job_profile").get(
        id=export_job_id
    )

    try:
        export_job.status = ApplicationExportJob.ExportStatus.PROCESSING
        export_job.save(update_fields=["status", "updated_at"])

        # Query applications
        qs = (
            JobApplication.objects.filter(
                job_profile=export_job.job_profile,
            )
            .select_related("address")
            .prefetch_related("answers__question")
        )

        if export_job.application_status:
            qs = qs.filter(status=export_job.application_status)

        qs = qs.order_by("-submitted_at")

        # Pre-fetch analyses
        app_ids = list(qs.values_list("id", flat=True))
        analyses_map = {}
        if app_ids:
            for analysis in ApplicationAnalysis.objects.filter(
                job_application_id__in=app_ids
            ):
                analyses_map[analysis.job_application_id] = analysis

        # Cache address on each app for column lambdas
        apps_list = list(qs)
        for app in apps_list:
            app._address_cache = getattr(app, "address", None)

        # Build rows
        headers = [col[0] for col in COLUMNS]

        # Also add Q&A columns dynamically
        qa_questions = []
        if apps_list:
            # Get all questions from the job profile
            qa_questions = list(
                export_job.job_profile.questions.order_by("order").values_list(
                    "id", "text"
                )
            )

        all_headers = headers + [q_text for _, q_text in qa_questions]

        rows = []
        for app in apps_list:
            analysis = analyses_map.get(app.id)
            row = [col_fn(app, analysis) for _, col_fn in COLUMNS]

            # Add Q&A answers
            answers_map = {
                str(a.question_id): (
                    a.answer_text or ", ".join(a.selected_choices or [])
                )
                for a in app.answers.all()
            }
            for q_id, _ in qa_questions:
                row.append(answers_map.get(str(q_id), ""))

            rows.append(row)

        # Generate file in memory / temp path then upload to storage
        from job_applications.storage import get_storage
        import tempfile

        status_label = export_job.application_status or "all"
        profile_title = export_job.job_profile.title.replace(" ", "_")[:30]
        base_name = f"{profile_title}_{status_label}_{export_job.id}"

        if export_job.export_format == ApplicationExportJob.ExportFormat.CSV:
            file_name = f"{base_name}.csv"
            content_type = "text/csv"
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(all_headers)
            writer.writerows(rows)
            file_bytes = buf.getvalue().encode("utf-8")
        else:
            # XLSX
            import openpyxl

            file_name = f"{base_name}.xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Applications"
            ws.append(all_headers)
            for row in rows:
                ws.append(row)
            for col_idx, header in enumerate(all_headers, 1):
                ws.column_dimensions[
                    openpyxl.utils.get_column_letter(col_idx)
                ].width = max(len(header) + 2, 12)
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            wb.save(tmp_path)
            file_bytes = tmp_path.read_bytes()
            tmp_path.unlink(missing_ok=True)

        storage_key, _ = get_storage().save_at_path(
            io.BytesIO(file_bytes),
            f"exports/{file_name}",
            content_type=content_type,
        )

        export_job.file_path = storage_key
        export_job.status = ApplicationExportJob.ExportStatus.DONE
        export_job.save(update_fields=["file_path", "status", "updated_at"])
        logger.info("Export completed: %s", storage_key)

    except Exception as exc:
        logger.exception("Export failed for job %s", export_job_id)
        export_job.status = ApplicationExportJob.ExportStatus.FAILED
        export_job.error_message = f"Export error: {exc}\n{traceback.format_exc()}"
        export_job.save(update_fields=["status", "error_message", "updated_at"])
