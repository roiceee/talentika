"""
Django management command to start the RQ workers for the analysis pipeline.

Usage:
    uv run python manage.py run_analysis_workers                      # all queues
    uv run python manage.py run_analysis_workers --queue ocr_queue
    uv run python manage.py run_analysis_workers --queue ai_queue
    uv run python manage.py run_analysis_workers --queue ai_queue --concurrency 20
    uv run python manage.py run_analysis_workers --queue export_queue
"""

import asyncio
import logging

from django.core.management.base import BaseCommand
from rq import Worker, Queue

from job_application_analysis.workers import _get_redis_connection

logger = logging.getLogger(__name__)


async def _run_ai_worker_async(concurrency: int):
    """
    Async worker loop for ``ai_queue``.

    Polls Redis for job IDs via BLPOP and dispatches up to ``concurrency``
    ``_process_ai_analysis_async`` coroutines concurrently.  Each coroutine
    awaits its own AsyncOpenAI HTTP call independently, so a single process
    can have many analyses in-flight at the same time without blocking.
    """
    import redis.asyncio as aioredis
    from django.conf import settings
    from rq.job import Job

    from job_application_analysis.workers import _process_ai_analysis_async

    async_conn = aioredis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_keepalive=True,
        health_check_interval=30,
    )
    sync_conn = _get_redis_connection()
    semaphore = asyncio.Semaphore(concurrency)

    async def handle(job_id: str):
        async with semaphore:
            try:
                job = await asyncio.to_thread(Job.fetch, job_id, sync_conn)
                application_analysis_id = job.args[0]
                await _process_ai_analysis_async(application_analysis_id)
            except Exception:
                logger.exception("Async AI worker: unhandled error for job %s", job_id)

    logger.info("Async AI worker started (concurrency=%d)", concurrency)
    while True:
        result = await async_conn.blpop("rq:queue:ai_queue", timeout=5)
        if result:
            _, job_id = result
            asyncio.create_task(handle(job_id))


class Command(BaseCommand):
    help = "Start RQ workers for the OCR, AI analysis, and export queues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            type=str,
            default=None,
            help="Listen on a specific queue only (ocr_queue, ai_queue, export_queue). Default: all.",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=10,
            help="Max concurrent jobs for the async ai_queue worker (default: 10).",
        )

    def handle(self, *args, **options):
        queue_name = options.get("queue")
        concurrency = options["concurrency"]

        if queue_name == "ai_queue":
            asyncio.run(_run_ai_worker_async(concurrency))
            return

        conn = _get_redis_connection()

        if queue_name:
            queues = [Queue(queue_name, connection=conn)]
            self.stdout.write(f"Starting worker on queue: {queue_name}")
        else:
            queues = [
                Queue("ocr_queue", connection=conn),
                Queue("ai_queue", connection=conn),
                Queue("export_queue", connection=conn),
            ]
            self.stdout.write("Starting worker on queues: ocr_queue, ai_queue, export_queue")

        worker = Worker(queues, connection=conn)
        worker.work(with_scheduler=False)
