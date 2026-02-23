"""
OCR service — extracts text from PDF files using doctr.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# doctr model singleton
# ---------------------------------------------------------------------------
_ocr_model = None
_model_lock = threading.Lock()


def _get_ocr_model():
    """Load the doctr OCR model once and reuse it across calls."""
    global _ocr_model
    if _ocr_model is not None:
        return _ocr_model
    with _model_lock:
        # Double-checked locking — another thread may have loaded it while we waited
        if _ocr_model is None:
            from doctr.models import ocr_predictor

            logger.info(
                "Loading doctr OCR model (this may download weights on first run)..."
            )
            _ocr_model = ocr_predictor(
                det_arch="db_resnet50",
                reco_arch="crnn_vgg16_bn",
                pretrained=True,
            )
            logger.info("doctr OCR model ready.")
    return _ocr_model


def warmup():
    """
    Pre-load the OCR model in the current process.

    Call this at startup (e.g. from AppConfig.ready or the RQ worker entry
    point) so the download/initialisation cost is paid once at boot time
    rather than on the first request.
    """
    _get_ocr_model()


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Given raw PDF bytes, return the extracted text as a single string.

    Pages are separated by ``\\n\\n--- Page N ---\\n\\n`` markers for
    downstream readability.
    """
    from doctr.io import DocumentFile

    model = _get_ocr_model()
    doc = DocumentFile.from_pdf(pdf_bytes)
    result = model(doc)

    pages: list[str] = []
    for page_idx, page in enumerate(result.pages):
        lines: list[str] = []
        for block in page.blocks:
            for line in block.lines:
                words = " ".join(w.value for w in line.words)
                lines.append(words)
        page_text = "\n".join(lines)
        pages.append(f"--- Page {page_idx + 1} ---\n{page_text}")

    return "\n\n".join(pages)


def extract_text_from_file(file_obj) -> str:
    """Accept a file-like object (e.g. Django ``UploadedFile``), read it,
    and return the extracted text."""
    file_obj.seek(0)
    return extract_text_from_pdf_bytes(file_obj.read())
