"""
Management command: inspect_queue

Shows a snapshot of the RQ queue depths and the ApplicationAnalysis status
distribution in the database.  Useful for diagnosing stuck / backed-up jobs
in production.

Usage:
    uv run python manage.py inspect_queue
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print RQ queue depths and ApplicationAnalysis status counts."

    def handle(self, *args, **options):
        self._check_queues()
        self.stdout.write("")
        self._check_db()

    # ------------------------------------------------------------------
    # Redis / RQ
    # ------------------------------------------------------------------

    def _check_queues(self):
        import ssl as ssl_module

        import redis
        from django.conf import settings
        from rq import Queue
        from rq.job import JobStatus

        ssl_enabled = getattr(settings, "REDIS_SSL", False)
        if ssl_enabled:
            conn = redis.Redis.from_url(
                settings.REDIS_URL, ssl_cert_reqs=ssl_module.CERT_NONE
            )
        else:
            conn = redis.Redis.from_url(settings.REDIS_URL)

        self.stdout.write(self.style.HTTP_INFO("─── Redis Queues ───────────────────────────"))
        try:
            conn.ping()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Redis unreachable: {exc}"))
            return

        for queue_name in ("ocr_queue", "ai_queue"):
            q = Queue(queue_name, connection=conn)
            queued    = q.count
            started   = q.started_job_registry.count
            failed    = q.failed_job_registry.count
            deferred  = q.deferred_job_registry.count
            scheduled = q.scheduled_job_registry.count

            self.stdout.write(
                f"  {queue_name:<20} "
                f"queued={queued}  started={started}  "
                f"failed={failed}  deferred={deferred}  scheduled={scheduled}"
            )

            if failed:
                self.stdout.write(
                    self.style.WARNING(f"    ↳ {failed} failed job(s) in {queue_name}:")
                )
                for job_id in q.failed_job_registry.get_job_ids():
                    self.stdout.write(f"      • {job_id}")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    def _check_db(self):
        from django.db.models import Count

        from job_application_analysis.models import ApplicationAnalysis

        self.stdout.write(self.style.HTTP_INFO("─── ApplicationAnalysis (DB) ───────────────"))

        rows = (
            ApplicationAnalysis.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        if not rows:
            self.stdout.write("  (no records)")
            return

        for row in rows:
            s     = row["status"]
            count = row["count"]
            style = self._status_style(s)
            self.stdout.write(f"  {style(s):<30} {count}")

        # List the most-recent FAILED ones with their error snippets
        failed_qs = ApplicationAnalysis.objects.filter(
            status=ApplicationAnalysis.Status.FAILED
        ).order_by("-updated_at")[:10]

        if failed_qs.exists():
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("  Recent FAILED analyses (up to 10):"))
            for a in failed_qs:
                snippet = (a.error_message or "—")[:120].replace("\n", " ")
                self.stdout.write(
                    f"    [{a.id}]  app={a.job_application_id}\n"
                    f"      updated={a.updated_at:%Y-%m-%d %H:%M:%S UTC}  error: {snippet}"
                )

        # List stuck in-progress analyses
        stuck_statuses = [
            ApplicationAnalysis.Status.OCR_PENDING,
            ApplicationAnalysis.Status.OCR_DONE,
            ApplicationAnalysis.Status.AI_PENDING,
        ]
        stuck_qs = ApplicationAnalysis.objects.filter(
            status__in=stuck_statuses
        ).order_by("updated_at")[:20]

        if stuck_qs.exists():
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("  Potentially stuck analyses (not terminal, up to 20):"))
            for a in stuck_qs:
                self.stdout.write(
                    f"    [{a.id}]  status={a.status}  "
                    f"updated={a.updated_at:%Y-%m-%d %H:%M:%S UTC}"
                )

    def _status_style(self, status_value):
        from job_application_analysis.models import ApplicationAnalysis

        return {
            ApplicationAnalysis.Status.DONE:        self.style.SUCCESS,
            ApplicationAnalysis.Status.FAILED:      self.style.ERROR,
            ApplicationAnalysis.Status.OCR_PENDING: self.style.WARNING,
            ApplicationAnalysis.Status.OCR_DONE:    self.style.WARNING,
            ApplicationAnalysis.Status.AI_PENDING:  self.style.WARNING,
            ApplicationAnalysis.Status.UPLOADED:    self.style.NOTICE,
        }.get(status_value, lambda x: x)
