"""
OCR service — extracts text from PDF files using pytesseract.
Supports DOCX input by converting to PDF first via LibreOffice.
"""

import logging
import os
import subprocess
import tempfile
import time

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
    logger.info("OCR: converting PDF to images (size=%d bytes)", len(pdf_bytes))
    t0 = time.monotonic()
    images = convert_from_bytes(pdf_bytes)
    logger.info("OCR: PDF rendered to %d page(s) in %.2fs", len(images), time.monotonic() - t0)

    pages: list[str] = []
    for page_idx, image in enumerate(images):
        logger.debug(
            "OCR: extracting text from page %d/%d (image size=%s)",
            page_idx + 1,
            len(images),
            image.size,
        )
        t_page = time.monotonic()
        page_text = pytesseract.image_to_string(image)
        logger.info(
            "OCR: page %d/%d done in %.2fs — %d chars extracted",
            page_idx + 1,
            len(images),
            time.monotonic() - t_page,
            len(page_text),
        )
        pages.append(f"--- Page {page_idx + 1} ---\n{page_text}")

    total_chars = sum(len(p) for p in pages)
    logger.info(
        "OCR: finished — %d page(s), %d total chars, %.2fs elapsed",
        len(images),
        total_chars,
        time.monotonic() - t0,
    )
    return "\n\n".join(pages)


def convert_docx_to_pdf_bytes(docx_bytes: bytes) -> bytes:
    """
    Convert a DOCX file (as raw bytes) to PDF bytes using LibreOffice.

    Requires ``libreoffice`` (``soffice``) to be installed on the system.
    Raises ``subprocess.CalledProcessError`` if conversion fails.
    """
    logger.info("LibreOffice: converting DOCX to PDF (size=%d bytes)", len(docx_bytes))
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, "resume.docx")
        with open(docx_path, "wb") as f:
            f.write(docx_bytes)

        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdir,
                docx_path,
            ],
            capture_output=True,
            timeout=120,
        )
        stdout = result.stdout.decode(errors="replace").strip()
        stderr = result.stderr.decode(errors="replace").strip()
        if stdout:
            logger.debug("LibreOffice stdout: %s", stdout)
        if result.returncode != 0:
            logger.error(
                "LibreOffice conversion failed (returncode=%d): %s",
                result.returncode,
                stderr,
            )
            raise RuntimeError(f"LibreOffice DOCX→PDF conversion failed: {stderr}")
        if stderr:
            logger.debug("LibreOffice stderr: %s", stderr)

        pdf_path = os.path.join(tmpdir, "resume.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

    logger.info(
        "LibreOffice: DOCX→PDF done in %.2fs (pdf size=%d bytes)",
        time.monotonic() - t0,
        len(pdf_bytes),
    )
    return pdf_bytes


def extract_text_from_file(file_obj) -> str:
    """Accept a file-like object (e.g. Django ``UploadedFile``), read it,
    and return the extracted text."""
    file_obj.seek(0)
    return extract_text_from_pdf_bytes(file_obj.read())
