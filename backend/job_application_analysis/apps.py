import threading

from django.apps import AppConfig


class JobApplicationAnalysisConfig(AppConfig):
    name = "job_application_analysis"

    def ready(self):
        """
        Verify Tesseract OCR is available at server startup so
        misconfiguration is detected early.
        """
        thread = threading.Thread(
            target=self._warmup_ocr,
            name="tesseract-warmup",
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _warmup_ocr():
        try:
            from job_application_analysis.ocr_service import warmup

            warmup()
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).exception(
                "Tesseract OCR warm-up check failed — OCR may not work."
            )
