"""Vertical splitting of a P&ID page into overlapping bands."""

from __future__ import annotations

import math
from pathlib import Path

import pymupdf

from .logger import get_logger
from .models import SplitBox

logger = get_logger(__name__)


def compute_split_boxes(
    page_width: float,
    page_height: float,
    overlap: float,
    split_count: int = 3,
) -> list[SplitBox]:
    """Compute vertical crop boxes with symmetric overlap.

    ``overlap`` is the fraction of the total page width that two adjacent
    bands should share. For a page of width W, the nominal one-third band
    is W/3. Each boundary is extended by overlap/2 on each side, so the
    actual overlap region between two adjacent bands is overlap * W.
    """
    if not 0.0 <= overlap < 1.0:
        raise ValueError(f"overlap must be in [0, 1), got {overlap}")
    if split_count < 1:
        raise ValueError(f"split_count must be >= 1, got {split_count}")

    base_width = page_width / split_count
    half_overlap = (overlap * page_width) / 2

    boxes: list[SplitBox] = []
    for i in range(split_count):
        # Nominal start and end of the i-th band
        nominal_start = i * base_width
        nominal_end = (i + 1) * base_width

        # Extend toward neighbors, clamped to the page edges
        x0 = max(0.0, nominal_start - half_overlap)
        x1 = min(page_width, nominal_end + half_overlap)

        boxes.append(
            SplitBox(
                x0=round(x0, 4),
                y0=0.0,
                x1=round(x1, 4),
                y1=round(page_height, 4),
                split_index=i,
            )
        )

    logger.info(
        "Computed %s split boxes for width=%.2f, overlap=%.2f%%",
        split_count,
        page_width,
        overlap * 100,
    )
    for box in boxes:
        logger.debug("Split box %s: x0=%.2f x1=%.2f", box.split_index, box.x0, box.x1)

    return boxes


def _split_pdf_path(output_dir: Path, page_number: int, split_index: int) -> Path:
    return output_dir / f"page_{page_number + 1}_part{split_index + 1}.pdf"


def _split_png_path(output_dir: Path, page_number: int, split_index: int) -> Path:
    return output_dir / f"page_{page_number + 1}_part{split_index + 1}.png"


def create_split_pdfs(
    doc: pymupdf.Document,
    output_dir: Path,
    page_number: int = 0,
    overlap: float = 0.15,
    split_count: int = 3,
    dpi: int = 150,
) -> tuple[list[SplitBox], list[Path], list[Path]]:
    """Create split PDFs and rendered PNGs for a single page.

    Returns (split_boxes, pdf_paths, png_paths).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    page = doc[page_number]
    page_width = page.rect.width
    page_height = page.rect.height

    boxes = compute_split_boxes(page_width, page_height, overlap, split_count)

    pdf_paths: list[Path] = []
    png_paths: list[Path] = []

    for box in boxes:
        clip = pymupdf.Rect(box.x0, box.y0, box.x1, box.y1)

        # Create a new document with a single page sized to the clip
        split_doc = pymupdf.open()
        split_page = split_doc.new_page(width=box.width, height=box.height)
        split_page.show_pdf_page(split_page.rect, doc, page_number, clip=clip)

        pdf_path = _split_pdf_path(output_dir, page_number, box.split_index)
        split_doc.save(pdf_path)
        split_doc.close()

        # Render the split to PNG for the LLM and for sanity checks
        split_doc = pymupdf.open(pdf_path)
        split_page = split_doc[0]
        pix = split_page.get_pixmap(dpi=dpi)

        png_path = _split_png_path(output_dir, page_number, box.split_index)
        pix.save(png_path)
        split_doc.close()

        pdf_paths.append(pdf_path)
        png_paths.append(png_path)

        logger.info(
            "Created split %s: %s + %s",
            box.split_index + 1,
            pdf_path.name,
            png_path.name,
        )

    return boxes, pdf_paths, png_paths


def is_in_overlap(
    x0: float,
    x1: float,
    split_index: int,
    boxes: list[SplitBox],
    overlap_width: float,
    page_width: float,
) -> tuple[bool, str | None]:
    """Determine whether a horizontal span is inside an overlap zone.

    The overlap zone for split ``i`` is the region where it overlaps with
    the previous or next split. We return (in_overlap, side) where side is
    'left' (overlap with previous split) or 'right' (overlap with next split).
    """
    half_overlap = overlap_width / 2

    if split_index > 0:
        # Overlap with previous split is the band just to the right of
        # the nominal boundary on this split
        boundary = (split_index * page_width) / len(boxes)
        left_zone_start = max(0.0, boundary - half_overlap)
        left_zone_end = boundary + half_overlap
        if x0 < left_zone_end and x1 > left_zone_start:
            return True, "left"

    if split_index < len(boxes) - 1:
        # Overlap with next split is the band just to the left of
        # the nominal boundary on this split
        boundary = ((split_index + 1) * page_width) / len(boxes)
        right_zone_start = boundary - half_overlap
        right_zone_end = min(page_width, boundary + half_overlap)
        if x0 < right_zone_end and x1 > right_zone_start:
            return True, "right"

    return False, None
