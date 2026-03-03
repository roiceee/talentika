"""
Management command: reset_stuck_analyses

Finds ``ApplicationAnalysis`` rows that are stuck in non-terminal processing
states (ocr_pending, ocr_done, ai_pending) — typically caused by the dev
server or RQ workers being killed mid-task — and re-queues them so the
pipeline can resume automatically.

Recovery strategy per status
─────────────────────────────
  ocr_pending  → OCR never finished  → reset to UPLOADED,  re-enqueue OCR
  ocr_done     → AI never queued     → keep OCR text,      re-enqueue AI
  ai_pending   → AI never finished   → reset to OCR_DONE,  re-enqueue AI
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from job_application_analysis.models import ApplicationAnalysis

logger = logging.getLogger(__name__)

STUCK_STATUSES = [
    ApplicationAnalysis.Status.OCR_PENDING,
    ApplicationAnalysis.Status.OCR_DONE,
    ApplicationAnalysis.Status.AI_PENDING,
]


class Command(BaseCommand):
    help = "Reset stuck analysis jobs and re-enqueue them in the pipeline."

    def handle(self, *args, **options):
        stuck = ApplicationAnalysis.objects.filter(status__in=STUCK_STATUSES)
        count = stuck.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stuck analyses found."))
            return

        self.stdout.write(
            self.style.WARNING(f"Found {count} stuck analysis job(s). Re-queuing…")
        )

        # Import lazily to avoid touching workers before Django is fully ready
        from job_application_analysis.workers import _enqueue_ai, enqueue_ocr

        reset_to_uploaded = []
        reset_to_ocr_done = []
        enqueue_ai_direct = []

        for analysis in stuck.iterator():
            status = analysis.status

            if status == ApplicationAnalysis.Status.OCR_PENDING:
                # OCR never completed — start from scratch
                analysis.status = ApplicationAnalysis.Status.UPLOADED
                analysis.error_message = ""
                reset_to_uploaded.append(analysis)

            elif status == ApplicationAnalysis.Status.OCR_DONE:
                # OCR text is already extracted — just re-enqueue AI
                enqueue_ai_direct.append(analysis)

            elif status == ApplicationAnalysis.Status.AI_PENDING:
                # AI task died — reset so process_ai_analysis can re-mark
                # it AI_PENDING cleanly when the worker picks it up
                analysis.status = ApplicationAnalysis.Status.OCR_DONE
                analysis.error_message = ""
                reset_to_ocr_done.append(analysis)

        now = timezone.now()

        # Reset rows in bulk (auto_now doesn't fire on bulk ops, so set explicitly)
        if reset_to_uploaded:
            ids = [a.id for a in reset_to_uploaded]
            ApplicationAnalysis.objects.filter(id__in=ids).update(
                status=ApplicationAnalysis.Status.UPLOADED,
                error_message="",
                updated_at=now,
            )
        if reset_to_ocr_done:
            ids = [a.id for a in reset_to_ocr_done]
            ApplicationAnalysis.objects.filter(id__in=ids).update(
                status=ApplicationAnalysis.Status.OCR_DONE,
                error_message="",
                updated_at=now,
            )

        # Re-enqueue
        for analysis in reset_to_uploaded:
            enqueue_ocr(str(analysis.id))
            self._log(analysis, "UPLOADED → re-enqueued OCR")

        for analysis in enqueue_ai_direct:
            _enqueue_ai(str(analysis.id))
            self._log(analysis, "OCR_DONE → re-enqueued AI")

        for analysis in reset_to_ocr_done:
            _enqueue_ai(str(analysis.id))
            self._log(analysis, "AI_PENDING → reset to OCR_DONE, re-enqueued AI")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {len(reset_to_uploaded)} re-queued for OCR, "
                f"{len(enqueue_ai_direct) + len(reset_to_ocr_done)} re-queued for AI."
            )
        )

    def _log(self, analysis: ApplicationAnalysis, msg: str):
        self.stdout.write(f"  [{analysis.id}] {msg}")
        logger.info("reset_stuck_analyses: %s — %s", analysis.id, msg)
