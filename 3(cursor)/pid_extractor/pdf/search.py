"""P&ID-specific text search using PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass

from pid_extractor.config import SEARCH_TERMS
from pid_extractor.models import BBox
from pid_extractor.pdf.extractor import PDFExtractor


@dataclass
class SearchHit:
    term: str
    page: int
    bbox: BBox
    context: str | None = None


class PIDTextSearch:
    """Search P&ID PDFs for engineering terminology."""

    def __init__(self, extractor: PDFExtractor, terms: list[str] | None = None) -> None:
        self.extractor = extractor
        self.terms = terms or SEARCH_TERMS

    def search_page(self, page_index: int) -> list[SearchHit]:
        page_number = page_index + 1
        hits: list[SearchHit] = []
        words = self.extractor.extract_words(page_index)
        full_text = " ".join(w.text for w in words)

        for term in self.terms:
            rects = self.extractor.search_text(page_index, term)
            for bbox in rects:
                context = self._find_context(words, bbox)
                hits.append(SearchHit(
                    term=term,
                    page=page_number,
                    bbox=bbox,
                    context=context,
                ))

        return hits

    def search_all_pages(self, page_filter: list[int] | None = None) -> list[SearchHit]:
        all_hits: list[SearchHit] = []
        for i in range(self.extractor.page_count):
            page_number = i + 1
            if page_filter and page_number not in page_filter:
                continue
            all_hits.extend(self.search_page(i))
        return all_hits

    def _find_context(self, words: list, bbox: BBox, radius: float = 100.0) -> str | None:
        """Find nearby words for search hit context."""
        cx, cy = bbox.center
        nearby = []
        for w in words:
            wx, wy = w.bbox.center
            dist = ((wx - cx) ** 2 + (wy - cy) ** 2) ** 0.5
            if dist <= radius:
                nearby.append(w.text)
        return " ".join(nearby[:20]) if nearby else None
