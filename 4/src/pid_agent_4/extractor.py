"""Text extraction and overlap tagging for P&ID PDFs."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from .logger import get_logger
from .models import ExtractedWord, SplitBox
from .splitter import is_in_overlap

logger = get_logger(__name__)


def _intersects_box(
    x0: float, x1: float, box: SplitBox
) -> bool:
    """Check if a horizontal span intersects a split box."""
    return x0 < box.x1 and x1 > box.x0


def _word_in_box_overlap(
    x0: float,
    x1: float,
    split_index: int,
    boxes: list[SplitBox],
    overlap_width: float,
    page_width: float,
) -> bool:
    """Return True if the word lies inside the overlap zone of the given split."""
    in_overlap, _ = is_in_overlap(x0, x1, split_index, boxes, overlap_width, page_width)
    return in_overlap


def extract_words(
    doc: pymupdf.Document,
    boxes: list[SplitBox],
    page_width: float,
    overlap: float,
    page_number: int = 0,
) -> list[ExtractedWord]:
    """Extract words from the source page and tag them with split membership.

    Extracting from the source page rather than from each split PDF avoids
    character-level truncation of words that sit on a split boundary. For each
    word we determine which split boxes it intersects, and whether those
    intersections fall in an overlap zone.
    """
    page = doc[page_number]
    raw = page.get_text("words")
    overlap_width = overlap * page_width

    words: list[ExtractedWord] = []

    # PyMuPDF returns 8-tuples:
    # (x0, y0, x1, y1, text, block_no, line_no, word_no)
    for item in raw:
        if len(item) < 5:
            continue
        x0, y0, x1, y1, text = item[:5]

        x0 = float(x0)
        y0 = float(y0)
        x1 = float(x1)
        y1 = float(y1)

        # Determine which splits this word belongs to and whether it is in an
        # overlap zone in any of those splits.
        splits: list[int] = []
        in_overlap = False
        overlap_zone: str | None = None

        for box in boxes:
            if _intersects_box(x0, x1, box):
                splits.append(box.split_index)
                if _word_in_box_overlap(x0, x1, box.split_index, boxes, overlap_width, page_width):
                    in_overlap = True
                    # The word is inside an overlap on this split; record a
                    # representative side (left/right). For a word appearing in
                    # multiple splits this may be ambiguous, but the flag is what
                    # matters downstream.
                    _, side = is_in_overlap(
                        x0, x1, box.split_index, boxes, overlap_width, page_width
                    )
                    if overlap_zone is None and side:
                        overlap_zone = side

        if not splits:
            # Word is outside any split box; should not happen for page-filling
            # boxes, but skip just in case.
            continue

        words.append(
            ExtractedWord(
                text=text,
                x0=round(x0, 4),
                y0=round(y0, 4),
                x1=round(x1, 4),
                y1=round(y1, 4),
                page_number=page_number,
                split_index=splits[0],
                splits=sorted(splits),
                in_overlap=in_overlap,
                overlap_zone=overlap_zone,
                source_x0=round(x0, 4),
                source_x1=round(x1, 4),
            )
        )

    logger.info("Extracted %s words from source page", len(words))
    return words


def extract_all_words(
    doc: pymupdf.Document,
    boxes: list[SplitBox],
    page_width: float,
    overlap: float,
    page_number: int = 0,
) -> list[ExtractedWord]:
    """Extract, flag, and deduplicate words from the source PDF.

    Since extraction is performed on the full source page, each physical word
    appears exactly once and no cross-split deduplication is required. The
    ``splits`` field records every split in which the word is visible.
    """
    words = extract_words(doc, boxes, page_width, overlap, page_number)
    logger.info(
        "Extracted %s unique words; %s in overlap zones",
        len(words),
        sum(1 for w in words if w.in_overlap),
    )
    return words
