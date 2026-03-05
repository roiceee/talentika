"""
OCR service — extracts text from PDF files using pytesseract.
"""

import logging

import pytesseract
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)


def warmup():
    """
    Verify that Tesseract is available on the system.

    Call this at startup (e.g. from AppConfig.ready or the RQ worker entry
    point) so any misconfiguration is detected early rather than on the
    first request.
    """
    version = pytesseract.get_tesseract_version()
    logger.info("Tesseract OCR ready (version %s).", version)


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Given raw PDF bytes, return the extracted text as a single string.

    Pages are separated by ``\\n\\n--- Page N ---\\n\\n`` markers for
    downstream readability.
    """
    images = convert_from_bytes(pdf_bytes)

    pages: list[str] = []
    for page_idx, image in enumerate(images):
        page_text = pytesseract.image_to_string(image)
        pages.append(f"--- Page {page_idx + 1} ---\n{page_text}")

    return "\n\n".join(pages)


def extract_text_from_file(file_obj) -> str:
    """Accept a file-like object (e.g. Django ``UploadedFile``), read it,
    and return the extracted text."""
    file_obj.seek(0)
    return extract_text_from_pdf_bytes(file_obj.read())
