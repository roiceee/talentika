"""
Django management command to start the RQ workers for the analysis pipeline.

Usage:
    uv run python manage.py run_analysis_workers          # both queues
    uv run python manage.py run_analysis_workers --queue ocr_queue
    uv run python manage.py run_analysis_workers --queue ai_queue
"""

from django.core.management.base import BaseCommand
from rq import Worker, Queue

from job_application_analysis.workers import _get_redis_connection


class Command(BaseCommand):
    help = "Start RQ workers for the OCR and AI analysis queues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            type=str,
            default=None,
            help="Listen on a specific queue only (ocr_queue or ai_queue). Default: both.",
        )

    def handle(self, *args, **options):
        conn = _get_redis_connection()

        queue_name = options.get("queue")
        if queue_name:
            queues = [Queue(queue_name, connection=conn)]
            self.stdout.write(f"Starting worker on queue: {queue_name}")
        else:
            queues = [
                Queue("ocr_queue", connection=conn),
                Queue("ai_queue", connection=conn),
            ]
            self.stdout.write("Starting worker on queues: ocr_queue, ai_queue")

        worker = Worker(queues, connection=conn)
        worker.work(with_scheduler=False)
