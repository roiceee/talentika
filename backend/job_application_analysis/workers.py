"""
RQ (Redis Queue) task functions for the OCR → AI analysis pipeline.

Queue layout:
  - ``ocr_queue``  — extracts text from resume PDFs
  - ``ai_queue``   — sends extracted text to OpenAI for structured analysis

Each function receives an ``application_analysis_id`` (UUID) and mutates the
corresponding ``ApplicationAnalysis`` row through its status state-machine.

Status flow:
  UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE
  Any step can transition to FAILED on error.
"""

import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _download_resume_bytes(storage_path: str) -> bytes:
    """
    Download the resume file from storage and return raw bytes.
    Supports both local and S3 backends.
    """
    from django.conf import settings

    backend_type = getattr(settings, "STORAGE_BACKEND", "local").lower()

    if backend_type == "s3":
        import boto3

        client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        response = client.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=storage_path
        )
        return response["Body"].read()
    else:
        # Local storage — read from MEDIA_ROOT
        from pathlib import Path

        full_path = Path(settings.MEDIA_ROOT) / storage_path
        return full_path.read_bytes()


def _get_resume_storage_path(job_application):
    """Return the storage path of the resume attachment for a job application."""
    from job_applications.models import ApplicationAttachment

    attachment = ApplicationAttachment.objects.filter(
        job_application=job_application,
        file_type=ApplicationAttachment.FileType.RESUME,
    ).first()
    if attachment is None:
        raise ValueError(
            f"No resume attachment found for application {job_application.id}"
        )
    return attachment.file  # CharField holding the storage path / S3 key


def _collect_qa_pairs(job_application):
    """Return a list of {question, answer} dicts for the AI prompt."""
    pairs = []
    for qa in job_application.answers.select_related("question").all():
        answer = qa.answer_text or ", ".join(qa.selected_choices or [])
        pairs.append({"question": qa.question.text, "answer": answer})
    return pairs


def _replace_resume_with_pdf(
    job_application, docx_storage_path: str, pdf_bytes: bytes
) -> str:
    """
    Persist converted PDF bytes to storage, delete the original DOCX,
    and update the ApplicationAttachment DB record.

    Returns the new PDF storage path.
    """
    from django.conf import settings
    from job_applications.models import ApplicationAttachment

    # Derive new path — preserve original casing of the base name
    base = docx_storage_path[:-5]  # strip the 5-char ".docx" (or ".DOCX")
    pdf_storage_path = base + ".pdf"

    backend_type = getattr(settings, "STORAGE_BACKEND", "local").lower()

    if backend_type == "s3":
        import boto3

        client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        client.put_object(
            Bucket=bucket,
            Key=pdf_storage_path,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        client.delete_object(Bucket=bucket, Key=docx_storage_path)
    else:
        from pathlib import Path

        media_root = Path(settings.MEDIA_ROOT)
        pdf_full_path = media_root / pdf_storage_path
        pdf_full_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_full_path.write_bytes(pdf_bytes)
        docx_full_path = media_root / docx_storage_path
        docx_full_path.unlink(missing_ok=True)

    # Update the attachment record
    attachment = ApplicationAttachment.objects.filter(
        job_application=job_application,
        file_type=ApplicationAttachment.FileType.RESUME,
    ).first()
    if attachment:
        old_name = attachment.file_name
        if old_name.lower().endswith(".docx"):
            attachment.file_name = old_name[:-5] + ".pdf"
        attachment.file = pdf_storage_path
        attachment.file_size = len(pdf_bytes)
        attachment.save(update_fields=["file", "file_name", "file_size"])

    logger.info("Replaced DOCX with PDF: %s → %s", docx_storage_path, pdf_storage_path)
    return pdf_storage_path


# ---------------------------------------------------------------------------
# Queue tasks
# ---------------------------------------------------------------------------


async def _process_ocr_async(application_analysis_id: str):
    """
    Core async OCR worker logic.

    All blocking operations (file I/O, LibreOffice, pytesseract, DB) run in
    threads via ``asyncio.to_thread`` so the event loop stays free to start
    other OCR jobs concurrently.
    """
    from job_application_analysis.models import ApplicationAnalysis
    from job_application_analysis.ocr_service import (
        convert_docx_to_pdf_bytes,
        extract_text_from_pdf_bytes,
    )

    analysis = await asyncio.to_thread(
        lambda: ApplicationAnalysis.objects.select_related("job_application").get(
            id=application_analysis_id
        )
    )

    try:
        # 1. Mark OCR_PENDING
        analysis.status = ApplicationAnalysis.Status.OCR_PENDING
        await asyncio.to_thread(
            lambda: analysis.save(update_fields=["status", "updated_at"])
        )
        logger.info("OCR started for analysis %s", analysis.id)

        # 2. Download resume
        storage_path = await asyncio.to_thread(
            lambda: _get_resume_storage_path(analysis.job_application)
        )
        logger.info("OCR worker: downloading resume from %s", storage_path)
        file_bytes = await asyncio.to_thread(
            lambda: _download_resume_bytes(storage_path)
        )
        logger.info(
            "OCR worker: downloaded %d bytes from %s", len(file_bytes), storage_path
        )

        # 3. Convert DOCX → PDF if necessary (LibreOffice subprocess)
        storage_path_lower = str(storage_path).lower()
        if storage_path_lower.endswith(".docx"):
            logger.info(
                "DOCX detected for analysis %s — converting to PDF via LibreOffice",
                analysis.id,
            )
            file_bytes = await asyncio.to_thread(
                lambda: convert_docx_to_pdf_bytes(file_bytes)
            )
            storage_path = await asyncio.to_thread(
                lambda: _replace_resume_with_pdf(
                    analysis.job_application, str(storage_path), file_bytes
                )
            )

        # 4. Extract text (pytesseract subprocess — CPU/I/O heavy)
        extracted = await asyncio.to_thread(
            lambda: extract_text_from_pdf_bytes(file_bytes)
        )

        # 5. Save
        analysis.extracted_resume_text = extracted
        analysis.status = ApplicationAnalysis.Status.OCR_DONE
        await asyncio.to_thread(
            lambda: analysis.save(
                update_fields=["extracted_resume_text", "status", "updated_at"]
            )
        )
        logger.info("OCR completed for analysis %s", analysis.id)

        # 6. Enqueue AI task
        await asyncio.to_thread(lambda: _enqueue_ai(str(analysis.id)))

    except Exception as exc:
        logger.exception("OCR failed for analysis %s", analysis.id)
        analysis.status = ApplicationAnalysis.Status.FAILED
        analysis.error_message = f"OCR error: {exc}\n{traceback.format_exc()}"
        await asyncio.to_thread(
            lambda: analysis.save(
                update_fields=["status", "error_message", "updated_at"]
            )
        )


def process_ocr(application_analysis_id: str):
    """
    OCR worker task — runs on the ``ocr_queue``.

    Sync wrapper around ``_process_ocr_async`` for compatibility with the
    standard RQ worker (used locally / in dev).
    In production the async worker loop in ``run_analysis_workers`` calls
    ``_process_ocr_async`` directly.
    """
    asyncio.run(_process_ocr_async(application_analysis_id))


async def _process_ai_analysis_async(application_analysis_id: str):
    """
    Core async AI worker logic.

    Called directly by the async worker loop in ``run_analysis_workers``.
    Multiple instances of this coroutine can run concurrently within a single
    process, each awaiting their own OpenAI HTTP call independently.
    """
    from job_application_analysis.models import ApplicationAnalysis
    from job_application_analysis.ai_service import (
        analyse_resume,
        BulkResumeAnalysisResult,
    )

    analysis = await asyncio.to_thread(
        lambda: ApplicationAnalysis.objects.select_related(
            "job_application__job_profile"
        ).get(id=application_analysis_id)
    )

    try:
        # 1. Mark AI_PENDING
        analysis.status = ApplicationAnalysis.Status.AI_PENDING
        await asyncio.to_thread(
            lambda: analysis.save(update_fields=["status", "updated_at"])
        )
        logger.info("AI analysis started for %s", analysis.id)

        job_app = analysis.job_application
        job_profile = job_app.job_profile

        is_bulk_upload = job_app.email.endswith("@bulk.internal")

        # 2. Collect context (DB reads — run in thread to avoid blocking event loop)
        qa_pairs = await asyncio.to_thread(lambda: _collect_qa_pairs(job_app))
        qualifications_list = await asyncio.to_thread(
            lambda: list(
                job_profile.qualifications.values(
                    "category",
                    "name",
                    "requirement_level",
                    "years_required",
                    "proficiency_level",
                )
            )
        )

        # 3. Call AI — this is the slow I/O step; truly async with AsyncOpenAI
        result = await analyse_resume(
            resume_text=analysis.extracted_resume_text,
            job_title=job_profile.title,
            job_description=job_profile.description,
            qualifications=qualifications_list,
            questions_and_answers=qa_pairs,
            is_bulk_upload=is_bulk_upload,
        )

        # 4. Back-fill contact info for bulk uploads
        if is_bulk_upload and isinstance(result, BulkResumeAnalysisResult):
            from job_applications.models import JobApplication as _JobApp

            info = result.applicant_info
            logger.info(
                "Bulk contact extraction for application %s: "
                "first_name=%r last_name=%r email=%r phone=%r",
                job_app.id,
                info.first_name,
                info.last_name,
                info.email,
                info.phone,
            )
            update_kwargs = {}
            if info.first_name:
                update_kwargs["first_name"] = info.first_name
            if info.last_name:
                update_kwargs["last_name"] = info.last_name
            if info.phone:
                update_kwargs["phone"] = info.phone
            if info.email:
                update_kwargs["email"] = info.email
            if update_kwargs:
                await asyncio.to_thread(
                    lambda: _JobApp.objects.filter(pk=job_app.pk).update(**update_kwargs)
                )
                logger.info(
                    "Back-filled contact info for application %s: %s",
                    job_app.id,
                    list(update_kwargs.keys()),
                )
            else:
                logger.warning(
                    "Bulk upload application %s: AI could not extract any contact info.",
                    job_app.id,
                )

        # 5. Persist and mark DONE
        analysis.ai_analysis_summary = result.ai_analysis_summary
        analysis.notable_traits = result.notable_traits
        analysis.key_skills = result.key_skills
        analysis.score_category = result.score_category
        analysis.detailed_analysis = result.detailed_analysis.model_dump()
        analysis.status = ApplicationAnalysis.Status.DONE
        await asyncio.to_thread(
            lambda: analysis.save(
                update_fields=[
                    "ai_analysis_summary",
                    "notable_traits",
                    "key_skills",
                    "score_category",
                    "detailed_analysis",
                    "status",
                    "updated_at",
                ]
            )
        )
        logger.info(
            "AI analysis completed for %s (category=%s)",
            analysis.id,
            result.score_category,
        )

    except Exception as exc:
        logger.exception("AI analysis failed for %s", analysis.id)
        analysis.status = ApplicationAnalysis.Status.FAILED
        analysis.error_message = f"AI error: {exc}\n{traceback.format_exc()}"
        await asyncio.to_thread(
            lambda: analysis.save(update_fields=["status", "error_message", "updated_at"])
        )


def process_ai_analysis(application_analysis_id: str):
    """
    AI worker task — runs on the ``ai_queue``.

    Sync wrapper around ``_process_ai_analysis_async`` for compatibility with
    the standard RQ worker (used locally / in dev).
    In production the async worker loop in ``run_analysis_workers`` calls
    ``_process_ai_analysis_async`` directly, bypassing this wrapper.
    """
    asyncio.run(_process_ai_analysis_async(application_analysis_id))


# ---------------------------------------------------------------------------
# Enqueue helpers (used by views / submission hook)
# ---------------------------------------------------------------------------


def _get_redis_connection():
    """Return a Redis connection from Django settings."""
    import redis
    from django.conf import settings

    # health_check_interval sends a periodic PING to prevent the server from
    # closing idle connections (common with managed providers like Upstash).
    kwargs = {
        "socket_keepalive": True,
        "health_check_interval": 30,
    }

    ssl_enabled = getattr(settings, "REDIS_SSL", False)
    if ssl_enabled:
        import ssl as ssl_module

        kwargs["ssl_cert_reqs"] = ssl_module.CERT_NONE
    return redis.Redis.from_url(settings.REDIS_URL, **kwargs)


def _enqueue_ai(application_analysis_id: str):
    """Enqueue the AI analysis task on ``ai_queue``."""
    from rq import Queue

    q = Queue("ai_queue", connection=_get_redis_connection())
    q.enqueue(process_ai_analysis, application_analysis_id)
    logger.info("Enqueued AI task for analysis %s", application_analysis_id)


def enqueue_ocr(application_analysis_id: str):
    """
    Public helper — enqueue the OCR task on ``ocr_queue``.

    Call this from the submission view after creating the
    ``ApplicationAnalysis`` row.
    """
    from rq import Queue
    from rq.job import Retry

    q = Queue("ocr_queue", connection=_get_redis_connection())
    q.enqueue(
        process_ocr,
        application_analysis_id,
        retry=Retry(max=3, interval=[30, 60, 120]),
    )
    logger.info("Enqueued OCR task for analysis %s", application_analysis_id)
