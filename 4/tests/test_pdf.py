"""Tests for PDF validation and inspection."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from pid_agent_4.exceptions import InvalidPDFError
from pid_agent_4.pdf import get_page_dimensions, is_vector_pdf, open_pdf, validate_pdf


def test_open_pdf(sample_pdf_path: Path):
    doc = open_pdf(sample_pdf_path)
    assert doc.page_count == 1
    doc.close()


def test_open_pdf_missing():
    with pytest.raises(InvalidPDFError):
        open_pdf(Path("/does/not/exist.pdf"))


def test_is_vector_pdf(sample_pdf_path: Path):
    doc = open_pdf(sample_pdf_path)
    assert is_vector_pdf(doc, page_number=0) is True
    doc.close()


def test_get_page_dimensions(sample_pdf_path: Path):
    doc = open_pdf(sample_pdf_path)
    width, height = get_page_dimensions(doc)
    assert width == 900.0
    assert height == 600.0
    doc.close()


def test_validate_pdf_accepts_vector(sample_pdf_path: Path):
    doc = open_pdf(sample_pdf_path)
    validate_pdf(doc)  # should not raise
    doc.close()


def test_validate_pdf_rejects_scanned_raster(tmp_path: Path):
    """A PDF containing only a full-page image and no text/drawings is rejected."""
    pdf_path = tmp_path / "raster.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=200, height=200)

    # Create a tiny raster image
    pix = pymupdf.Pixmap(pymupdf.csGRAY, 200, 200, b"\x80" * (200 * 200), False)
    img_filename = tmp_path / "raster.png"
    pix.save(img_filename)

    # Insert full-page image
    rect = page.rect
    page.insert_image(rect, filename=img_filename)
    doc.save(pdf_path)
    doc.close()

    doc = open_pdf(pdf_path)
    assert not is_vector_pdf(doc, page_number=0)
    with pytest.raises(InvalidPDFError):
        validate_pdf(doc, page_number=0)
    doc.close()
