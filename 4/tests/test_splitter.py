"""Tests for the vertical splitter."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pid_agent_4.splitter import compute_split_boxes, create_split_pdfs


def test_compute_split_boxes_three_way():
    boxes = compute_split_boxes(900, 600, 0.15)
    assert len(boxes) == 3

    # First box starts at 0
    assert boxes[0].x0 == 0.0
    # Last box ends at page width
    assert boxes[-1].x1 == 900.0

    # Overlap region between split 0 and 1 should be 0.15 * 900 = 135
    assert math.isclose(boxes[0].x1 - boxes[1].x0, 0.15 * 900, rel_tol=1e-4)
    assert math.isclose(boxes[1].x1 - boxes[2].x0, 0.15 * 900, rel_tol=1e-4)

    # Each boundary is centered on the nominal 1/3 line
    assert math.isclose((boxes[0].x1 + boxes[1].x0) / 2, 300.0, rel_tol=1e-4)
    assert math.isclose((boxes[1].x1 + boxes[2].x0) / 2, 600.0, rel_tol=1e-4)


def test_compute_split_boxes_no_overlap():
    boxes = compute_split_boxes(900, 600, 0.0)
    assert len(boxes) == 3
    assert boxes[0].x1 == boxes[1].x0
    assert boxes[1].x1 == boxes[2].x0


def test_create_split_pdfs(sample_pdf_path: Path, tmp_path: Path):
    doc = __import__("pymupdf").open(sample_pdf_path)
    output_dir = tmp_path / "splits"
    boxes, pdf_paths, png_paths = create_split_pdfs(doc, output_dir, dpi=72)

    assert len(boxes) == 3
    assert len(pdf_paths) == 3
    assert len(png_paths) == 3

    for pdf in pdf_paths:
        assert pdf.exists()
    for png in png_paths:
        assert png.exists()

    # Verify each split contains one page
    for pdf in pdf_paths:
        split_doc = __import__("pymupdf").open(pdf)
        assert split_doc.page_count == 1
        split_doc.close()

    doc.close()
