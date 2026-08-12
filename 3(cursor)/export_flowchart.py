#!/usr/bin/env python3
"""Convert flowchart SVG to PDF and ensure JPG exists in output/."""

from __future__ import annotations

import shutil
from pathlib import Path

import fitz  # PyMuPDF


def svg_to_pdf(svg_path: Path, pdf_path: Path) -> None:
    """Render SVG to PDF using PyMuPDF."""
    doc = fitz.open(str(svg_path))
    pdf_bytes = doc.convert_to_pdf()
    pdf_path.write_bytes(pdf_bytes)
    doc.close()


def main() -> None:
    base = Path(__file__).parent
    out = base / "output"
    svg = out / "123_flowchart.svg"
    jpg = out / "123_flowchart.jpg"
    pdf = out / "123_flowchart.pdf"

    # Copy AI-generated JPG from assets if missing
    assets_jpg = Path(r"C:\Users\amitv\.cursor\projects\c-Users-amitv-Desktop-PHA-Pro-PDF\assets\123_flowchart.jpg")
    if assets_jpg.exists() and (not jpg.exists() or jpg.stat().st_size < 1000):
        shutil.copy2(assets_jpg, jpg)
        print(f"Copied JPG: {jpg}")

    # Matplotlib version (higher fidelity)
    try:
        from generate_flowchart import load_entities, draw_flowchart
        json_path = out / "123_structured.json"
        if json_path.exists():
            entities = load_entities(json_path)
            draw_flowchart(entities, jpg, pdf)
            print("Generated via matplotlib.")
            return
    except ImportError:
        pass

    # Fallback: SVG → PDF via PyMuPDF
    if svg.exists():
        svg_to_pdf(svg, pdf)
        print(f"Saved PDF: {pdf}")

    if not jpg.exists() and assets_jpg.exists():
        shutil.copy2(assets_jpg, jpg)


if __name__ == "__main__":
    main()
