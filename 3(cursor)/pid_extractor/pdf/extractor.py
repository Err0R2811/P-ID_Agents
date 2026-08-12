"""PyMuPDF PDF extraction layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from pid_extractor.models import BBox, Span, TextBlock, Word


class PDFExtractor:
    """Extract text, layout, and metadata from P&ID PDF pages."""

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        self.doc = fitz.open(str(self.pdf_path))

    @property
    def page_count(self) -> int:
        return len(self.doc)

    @property
    def filename(self) -> str:
        return self.pdf_path.name

    def get_page_size(self, page_index: int) -> tuple[float, float]:
        page = self.doc[page_index]
        rect = page.rect
        return rect.width, rect.height

    def extract_words(self, page_index: int) -> list[Word]:
        """Extract word-level text with coordinates."""
        page = self.doc[page_index]
        page_number = page_index + 1
        words: list[Word] = []
        for w in page.get_text("words"):
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            if not text.strip():
                continue
            words.append(Word(
                text=text,
                x0=x0, y0=y0, x1=x1, y1=y1,
                block_no=block_no,
                line_no=line_no,
                word_no=word_no,
                page=page_number,
            ))
        return words

    def extract_layout(self, page_index: int) -> list[TextBlock]:
        """Extract block > line > span hierarchy."""
        page = self.doc[page_index]
        page_number = page_index + 1
        data = page.get_text("dict")
        blocks: list[TextBlock] = []

        for block_idx, block in enumerate(data.get("blocks", [])):
            if block.get("type") != 0:  # text block only
                continue
            bbox = BBox.from_rect(tuple(block["bbox"]))
            lines_data: list[dict[str, Any]] = []
            spans: list[Span] = []

            for line_idx, line in enumerate(block.get("lines", [])):
                line_spans = []
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    s = Span(
                        text=text,
                        bbox=BBox.from_rect(tuple(span["bbox"])),
                        font=span.get("font", ""),
                        font_size=span.get("size", 0.0),
                        flags=span.get("flags", 0),
                        color=span.get("color", 0),
                        block_no=block_idx,
                        line_no=line_idx,
                        page=page_number,
                    )
                    spans.append(s)
                    line_spans.append(s.to_dict())
                if line_spans:
                    lines_data.append({
                        "line_no": line_idx,
                        "bbox": BBox.from_rect(tuple(line["bbox"])).to_dict(),
                        "spans": line_spans,
                    })

            if lines_data:
                blocks.append(TextBlock(
                    block_no=block_idx,
                    page=page_number,
                    bbox=bbox,
                    lines=lines_data,
                ))

        return blocks

    def extract_spans(self, page_index: int) -> list[Span]:
        """Flat list of all spans on a page."""
        spans: list[Span] = []
        for block in self.extract_layout(page_index):
            for line in block.lines:
                for span_dict in line.get("spans", []):
                    bbox = span_dict["bbox"]
                    spans.append(Span(
                        text=span_dict["text"],
                        bbox=BBox(
                            x0=bbox["x0"], y0=bbox["y0"],
                            x1=bbox["x1"], y1=bbox["y1"],
                        ),
                        font=span_dict.get("font", ""),
                        font_size=span_dict.get("font_size", 0.0),
                        flags=span_dict.get("flags", 0),
                        color=span_dict.get("color", 0),
                        block_no=block.block_no,
                        line_no=line.get("line_no", 0),
                        page=block.page,
                    ))
        return spans

    def extract_drawings(self, page_index: int) -> list[dict[str, Any]]:
        """Extract vector drawing paths from page."""
        page = self.doc[page_index]
        drawings = page.get_drawings()
        result = []
        for i, d in enumerate(drawings):
            rect = d.get("rect")
            items = d.get("items", [])
            result.append({
                "index": i,
                "rect": list(rect) if rect else None,
                "items": len(items),
                "type": d.get("type", "path"),
                "color": d.get("color"),
                "width": d.get("width"),
                "fill": d.get("fill"),
            })
        return result

    def extract_drawing_paths(self, page_index: int) -> list[list[tuple[float, float]]]:
        """Extract line/path point sequences for connection analysis."""
        page = self.doc[page_index]
        paths: list[list[tuple[float, float]]] = []
        for drawing in page.get_drawings():
            points: list[tuple[float, float]] = []
            for item in drawing.get("items", []):
                op = item[0]
                if op == "l" and len(item) >= 3:
                    points.append((item[1], item[2]))
                elif op == "re" and len(item) >= 5:
                    x, y, w, h = item[1], item[2], item[3], item[4]
                    points.extend([(x, y), (x + w, y + h)])
                elif op == "c" and len(item) >= 7:
                    points.append((item[-2], item[-1]))
            if len(points) >= 2:
                paths.append(points)
        return paths

    def search_text(self, page_index: int, query: str) -> list[BBox]:
        """Search for text on page, return bounding boxes."""
        page = self.doc[page_index]
        rects = page.search_for(query)
        return [BBox.from_rect(tuple(r)) for r in rects]

    def has_text_layer(self, page_index: int) -> bool:
        words = self.extract_words(page_index)
        return len(words) > 0

    def close(self) -> None:
        self.doc.close()

    def __enter__(self) -> PDFExtractor:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
