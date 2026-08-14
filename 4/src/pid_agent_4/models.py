"""Pydantic models for P&ID data."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SplitBox(BaseModel):
    """A crop box for a single vertical split."""

    x0: float
    y0: float
    x1: float
    y1: float
    page_number: int = 0
    split_index: int = 0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def rect(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


class ExtractedWord(BaseModel):
    """A word extracted from a split PDF with its source coordinates."""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_number: int = 0
    split_index: int
    splits: list[int] = []  # all split indices where this word was seen
    in_overlap: bool = False
    overlap_zone: str | None = None  # 'left' or 'right' when in_overlap
    source_x0: float | None = None  # original coordinate on source page
    source_x1: float | None = None

    def rect(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    def source_rect(self) -> tuple[float, float, float, float]:
        sx0 = self.source_x0 if self.source_x0 is not None else self.x0
        sx1 = self.source_x1 if self.source_x1 is not None else self.x1
        return (sx0, self.y0, sx1, self.y1)


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class PIDConnection(BaseModel):
    """A connection between two P&ID elements."""

    source_tag: str
    source_name: str | None = None
    target_tag: str
    target_name: str | None = None
    line_number: str | None = None
    line_type: str | None = None
    connection_type: str | None = None
    bbox: BoundingBox | None = None
    notes: str | None = None

    def fingerprint(self) -> str:
        """Stable key for deduplication."""
        return "|".join(
            [
                (self.source_tag or "").upper(),
                (self.target_tag or "").upper(),
                (self.line_number or "").upper(),
            ]
        )


class AgentResult(BaseModel):
    """Final combined result from both LLM calls."""

    markdown: str
    connections: list[PIDConnection] = Field(default_factory=list)
