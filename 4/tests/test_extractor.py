"""Tests for word extraction and overlap tagging."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from pid_agent_4.extractor import extract_all_words
from pid_agent_4.splitter import compute_split_boxes


def test_extract_all_words_unique_and_overlap(sample_pdf_path: Path):
    doc = pymupdf.open(sample_pdf_path)
    page = doc[0]
    width = page.rect.width

    boxes = compute_split_boxes(width, page.rect.height, 0.15)
    words = extract_all_words(doc, boxes, width, 0.15)

    # The synthetic PDF has 6 words
    assert len(words) == 6

    # Boundary words should be marked in overlap
    boundary_words = {"V-102", "T-103", "LINE-002", "LINE-003"}
    for w in words:
        if w.text in boundary_words:
            assert w.in_overlap, f"{w.text} should be in overlap"
            assert len(w.splits) >= 2
        else:
            assert not w.in_overlap, f"{w.text} should not be in overlap"

    # Every word should have source coordinates
    for w in words:
        assert w.source_x0 is not None
        assert w.source_x1 is not None

    doc.close()
