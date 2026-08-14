"""PDF validation and page inspection."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from .exceptions import InvalidPDFError
from .logger import get_logger

logger = get_logger(__name__)


def open_pdf(pdf_path: Path) -> pymupdf.Document:
    """Open a PDF and return a PyMuPDF Document."""
    path = Path(pdf_path)
    if not path.exists():
        raise InvalidPDFError(f"File not found: {path}")
    if not path.is_file():
        raise InvalidPDFError(f"Not a file: {path}")

    try:
        doc = pymupdf.open(path)
    except Exception as exc:  # pymupdf does not expose a base error in all versions
        raise InvalidPDFError(f"Could not open PDF: {exc}") from exc

    if doc.page_count == 0:
        raise InvalidPDFError("PDF has no pages")

    return doc


def get_page_dimensions(doc: pymupdf.Document, page_number: int = 0) -> tuple[float, float]:
    """Return (width, height) of the page in PDF points."""
    page = doc[page_number]
    rect = page.rect
    return rect.width, rect.height


def is_vector_pdf(doc: pymupdf.Document, page_number: int = 0) -> bool:
    """Check that the page looks like a vector PDF rather than a scanned image.

    A CAD-exported P&ID should contain text and/or vector drawing commands.
    We accept the page as vector if it contains at least one text block or
    any vector drawing commands.
    """
    page = doc[page_number]

    text = page.get_text("blocks")
    has_text = len(text) > 0

    drawings = page.get_drawings()
    has_drawings = len(drawings) > 0

    images = page.get_images()
    has_images = len(images) > 0

    # If the page has text or drawings, treat it as vector.
    # If it has only full-page images and no text/drawings, it is likely scanned.
    if has_text or has_drawings:
        logger.debug(
            "Page %s looks vector-based: text_blocks=%s drawings=%s",
            page_number,
            len(text),
            len(drawings),
        )
        return True

    if has_images and not (has_text or has_drawings):
        logger.warning(
            "Page %s appears to be a raster image with no text/drawings; likely scanned.",
            page_number,
        )
        return False

    # Fallback: no text, no drawings, no images -> empty/unknown.
    return False


def validate_pdf(doc: pymupdf.Document, page_number: int = 0) -> None:
    """Validate that the PDF can be processed."""
    if doc.page_count <= page_number:
        raise InvalidPDFError(f"Page {page_number} does not exist in PDF with {doc.page_count} pages")

    if not is_vector_pdf(doc, page_number):
        raise InvalidPDFError(
            "PDF page appears to be scanned/raster. This tool requires vector-based "
            "P&ID PDFs with extractable text or drawing commands."
        )
