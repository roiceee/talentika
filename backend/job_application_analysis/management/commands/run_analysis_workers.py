"""
Django management command to start the RQ workers for the analysis pipeline.

Usage:
    uv run python manage.py run_analysis_workers                      # all queues
    uv run python manage.py run_analysis_workers --queue ocr_queue
    uv run python manage.py run_analysis_workers --queue ocr_queue --concurrency 4
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


async def _run_async_worker(queue_name: str, concurrency: int):
    """
    Generic async worker loop for a single queue.

    Polls Redis for job IDs via BLPOP and dispatches up to ``concurrency``
    coroutines concurrently.  Each coroutine runs its blocking work in threads
    via ``asyncio.to_thread``, so the event loop stays free to start new jobs
    while existing ones are waiting on I/O (OpenAI, pytesseract, S3, etc.).
    """
    import redis.asyncio as aioredis
    from django.conf import settings
    from rq.job import Job

    from job_application_analysis.workers import (
        _process_ocr_async,
        _process_ai_analysis_async,
    )

    handlers = {
        "ocr_queue": _process_ocr_async,
        "ai_queue": _process_ai_analysis_async,
    }
    handler = handlers[queue_name]

    async_conn_kwargs = {
        "decode_responses": True,
        "socket_keepalive": True,
        "health_check_interval": 30,
    }
    if getattr(settings, "REDIS_SSL", False):
        import ssl as ssl_module
        async_conn_kwargs["ssl_cert_reqs"] = ssl_module.CERT_NONE

    async_conn = aioredis.Redis.from_url(settings.REDIS_URL, **async_conn_kwargs)
    sync_conn = _get_redis_connection()
    semaphore = asyncio.Semaphore(concurrency)

    async def handle(job_id: str):
        async with semaphore:
            try:
                job = await asyncio.to_thread(Job.fetch, job_id, sync_conn)
                application_analysis_id = job.args[0]
                await handler(application_analysis_id)
            except Exception:
                logger.exception(
                    "Async worker (%s): unhandled error for job %s", queue_name, job_id
                )

    logger.info("Async worker started (queue=%s, concurrency=%d)", queue_name, concurrency)
    while True:
        result = await async_conn.blpop(f"rq:queue:{queue_name}", timeout=5)
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
            help=(
                "Max concurrent jobs for async queue workers (ocr_queue, ai_queue). "
                "Recommended: 4 for ocr_queue, 10+ for ai_queue. Default: 10."
            ),
        )

    def handle(self, *args, **options):
        queue_name = options.get("queue")
        concurrency = options["concurrency"]

        if queue_name in ("ocr_queue", "ai_queue"):
            asyncio.run(_run_async_worker(queue_name, concurrency))
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
