"""Page rendering with caching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


class PageRenderer:
    """Render PDF pages to images for visual analysis."""

    def __init__(
        self,
        doc: fitz.Document,
        output_dir: str | Path = "output/rendered",
        dpi: int = 150,
        cache: bool = True,
    ) -> None:
        self.doc = doc
        self.output_dir = Path(output_dir)
        self.dpi = dpi
        self.cache = cache
        self._cache: dict[int, str] = {}
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_page(self, page_index: int) -> tuple[str, fitz.Pixmap]:
        """Render page to PNG. Returns (path, pixmap)."""
        if self.cache and page_index in self._cache:
            path = self._cache[page_index]
            return path, fitz.Pixmap(path)

        page = self.doc[page_index]
        zoom = self.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        page_number = page_index + 1
        filename = f"page_{page_number:04d}_{self.dpi}dpi.png"
        path = str(self.output_dir / filename)
        pixmap.save(path)

        if self.cache:
            self._cache[page_index] = path

        return path, pixmap

    def get_page_image_size(self, page_index: int) -> tuple[int, int]:
        page = self.doc[page_index]
        zoom = self.dpi / 72.0
        return int(page.rect.width * zoom), int(page.rect.height * zoom)

    def clear_cache(self) -> None:
        self._cache.clear()
