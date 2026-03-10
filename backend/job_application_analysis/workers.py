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


# ---------------------------------------------------------------------------
# Queue tasks
# ---------------------------------------------------------------------------


def process_ocr(application_analysis_id: str):
    """
    OCR worker task — runs on the ``ocr_queue``.

    1. Set status → OCR_PENDING
    2. Download the resume PDF from storage
    3. Extract text via doctr
    4. Save extracted text, set status → OCR_DONE
    5. Enqueue the AI analysis task on ``ai_queue``
    """
    from job_application_analysis.models import ApplicationAnalysis
    from job_application_analysis.ocr_service import extract_text_from_pdf_bytes

    analysis = ApplicationAnalysis.objects.select_related("job_application").get(
        id=application_analysis_id
    )

    try:
        # 1. Mark OCR_PENDING
        analysis.status = ApplicationAnalysis.Status.OCR_PENDING
        analysis.save(update_fields=["status", "updated_at"])
        logger.info("OCR started for analysis %s", analysis.id)

        # 2. Download resume
        storage_path = _get_resume_storage_path(analysis.job_application)
        pdf_bytes = _download_resume_bytes(storage_path)

        # 3. Extract text
        extracted = extract_text_from_pdf_bytes(pdf_bytes)

        # 4. Save
        analysis.extracted_resume_text = extracted
        analysis.status = ApplicationAnalysis.Status.OCR_DONE
        analysis.save(update_fields=["extracted_resume_text", "status", "updated_at"])
        logger.info("OCR completed for analysis %s", analysis.id)

        # 5. Enqueue AI task
        _enqueue_ai(str(analysis.id))

    except Exception as exc:
        logger.exception("OCR failed for analysis %s", analysis.id)
        analysis.status = ApplicationAnalysis.Status.FAILED
        analysis.error_message = f"OCR error: {exc}\n{traceback.format_exc()}"
        analysis.save(update_fields=["status", "error_message", "updated_at"])


def process_ai_analysis(application_analysis_id: str):
    """
    AI worker task — runs on the ``ai_queue``.

    1. Set status → AI_PENDING
    2. Collect job profile + application data
    3. Call OpenAI structured output
    4. Persist result fields, set status → DONE
    """
    from job_application_analysis.models import ApplicationAnalysis
    from job_application_analysis.ai_service import analyse_resume

    analysis = ApplicationAnalysis.objects.select_related(
        "job_application__job_profile"
    ).get(id=application_analysis_id)

    try:
        # 1. Mark AI_PENDING
        analysis.status = ApplicationAnalysis.Status.AI_PENDING
        analysis.save(update_fields=["status", "updated_at"])
        logger.info("AI analysis started for %s", analysis.id)

        job_app = analysis.job_application
        job_profile = job_app.job_profile

        # 2. Collect context
        qa_pairs = _collect_qa_pairs(job_app)

        # Build qualifications list from the new Qualification model
        qualifications_list = list(
            job_profile.qualifications.values(
                "category",
                "name",
                "requirement_level",
                "years_required",
                "proficiency_level",
            )
        )

        # 3. Call AI
        result = analyse_resume(
            resume_text=analysis.extracted_resume_text,
            job_title=job_profile.title,
            job_description=job_profile.description,
            qualifications=qualifications_list,
            questions_and_answers=qa_pairs,
        )

        # 4. Persist
        analysis.ai_analysis_summary = result.ai_analysis_summary
        analysis.notable_traits = result.notable_traits
        analysis.key_skills = result.key_skills
        analysis.score = result.score
        analysis.detailed_analysis = result.detailed_analysis.model_dump()
        analysis.status = ApplicationAnalysis.Status.DONE
        analysis.save(
            update_fields=[
                "ai_analysis_summary",
                "notable_traits",
                "key_skills",
                "score",
                "detailed_analysis",
                "status",
                "updated_at",
            ]
        )
        logger.info(
            "AI analysis completed for %s (score=%s)", analysis.id, result.score
        )

    except Exception as exc:
        logger.exception("AI analysis failed for %s", analysis.id)
        analysis.status = ApplicationAnalysis.Status.FAILED
        analysis.error_message = f"AI error: {exc}\n{traceback.format_exc()}"
        analysis.save(update_fields=["status", "error_message", "updated_at"])


# ---------------------------------------------------------------------------
# Enqueue helpers (used by views / submission hook)
# ---------------------------------------------------------------------------


def _get_redis_connection():
    """Return a Redis connection from Django settings."""
    import redis
    from django.conf import settings

    ssl_enabled = getattr(settings, "REDIS_SSL", False)
    if ssl_enabled:
        import ssl as ssl_module
        return redis.Redis.from_url(
            settings.REDIS_URL,
            ssl_cert_reqs=ssl_module.CERT_NONE,
        )
    return redis.Redis.from_url(settings.REDIS_URL)


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

    q = Queue("ocr_queue", connection=_get_redis_connection())
    q.enqueue(process_ocr, application_analysis_id)
    logger.info("Enqueued OCR task for analysis %s", application_analysis_id)
