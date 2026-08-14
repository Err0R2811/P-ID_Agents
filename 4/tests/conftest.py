"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Create a synthetic vector P&ID PDF."""
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=900, height=600)

    # Add some equipment/instrument labels
    page.insert_text((50, 50), "PUMP-101")
    page.insert_text((350, 50), "V-102")
    page.insert_text((650, 50), "T-103")

    # Add line labels
    page.insert_text((50, 300), "LINE-001")
    page.insert_text((350, 300), "LINE-002")
    page.insert_text((650, 300), "LINE-003")

    # Draw a connecting line
    page.draw_line((100, 100), (800, 100))

    doc.save(pdf_path)
    doc.close()

    return pdf_path
