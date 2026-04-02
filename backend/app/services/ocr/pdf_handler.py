"""PDF processing utilities for OCR pipeline.

Handles text extraction from digital PDFs and image conversion for scanned PDFs.
Kept separate from pipeline.py to respect the 600-LOC limit.
"""

import asyncio
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
    """Use PyMuPDF (fitz) to extract text. Returns (text, page_count)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is not installed. Run: pip install PyMuPDF==1.24.9"
        )

    def _extract(data: bytes) -> Tuple[str, int]:
        doc = fitz.open(stream=data, filetype="pdf")
        page_count = len(doc)
        texts = []
        for page in doc:
            try:
                texts.append(page.get_text())
            except Exception:
                texts.append("")  # treat unreadable page as blank
        doc.close()
        return "\n".join(texts), page_count

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract, pdf_bytes)


def is_text_pdf(text: str, page_count: int) -> bool:
    """True if avg chars/page >= 50. Distinguishes digital vs scanned PDFs."""
    if page_count == 0:
        return False
    return (len(text) / page_count) >= 50


async def convert_pdf_pages_to_images(pdf_bytes: bytes) -> List[bytes]:
    """
    Convert each PDF page to JPEG bytes using PyMuPDF's built-in pixmap renderer.
    No Poppler or pdf2image required — fitz renders pages natively.
    Process one page at a time to avoid OOM on Render's 512MB free tier.
    dpi=200 (matrix scale 200/72 ≈ 2.78) is sufficient for OCR quality.
    Wraps blocking CPU call in run_in_executor.
    """
    import fitz  # PyMuPDF — already used above, guaranteed installed

    def _render_all_pages(data: bytes) -> List[bytes]:
        doc = fitz.open(stream=data, filetype="pdf")
        results: List[bytes] = []
        mat = fitz.Matrix(200 / 72, 200 / 72)  # 200 DPI
        for i, page in enumerate(doc):
            try:
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                results.append(pix.tobytes("jpeg"))
            except Exception as e:
                logger.warning(f"[PDF] Skipping page {i + 1} — render failed: {e}")
        doc.close()
        if not results:
            raise ValueError("PDF rendering produced no usable pages")
        return results

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _render_all_pages, pdf_bytes)


async def process_pdf_for_ocr(pdf_bytes: bytes) -> Tuple[str, List[bytes]]:
    """
    Orchestrator.
    - Digital PDF  → returns (extracted_text, [])
    - Scanned PDF  → returns ("", [page1_jpeg, page2_jpeg, ...])
    """
    text, page_count = await extract_text_from_pdf(pdf_bytes)
    if is_text_pdf(text, page_count):
        logger.info(
            f"[PDF] Digital PDF detected — {page_count} pages, {len(text)} chars"
        )
        return text, []
    else:
        logger.info(
            f"[PDF] Scanned PDF detected — {page_count} pages, converting to images"
        )
        page_images = await convert_pdf_pages_to_images(pdf_bytes)
        return "", page_images
