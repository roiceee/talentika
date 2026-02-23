import threading

from django.apps import AppConfig


class JobApplicationAnalysisConfig(AppConfig):
    name = "job_application_analysis"

    def ready(self):
        """
        Pre-warm the doctr OCR model in a daemon thread so the weights are
        downloaded and loaded at server startup, not on the first request.
        """
        thread = threading.Thread(
            target=self._warmup_ocr,
            name="doctr-warmup",
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
                "doctr OCR warm-up failed — model will load on first use instead."
            )
