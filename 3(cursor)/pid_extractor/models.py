"""Data models for P&ID extraction results."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _new_id(prefix: str = "ent") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def to_dict(self) -> dict[str, float]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @classmethod
    def from_rect(cls, rect: tuple[float, float, float, float]) -> BBox:
        return cls(x0=rect[0], y0=rect[1], x1=rect[2], y1=rect[3])

    def expand(self, margin: float) -> BBox:
        return BBox(
            x0=self.x0 - margin,
            y0=self.y0 - margin,
            x1=self.x1 + margin,
            y1=self.y1 + margin,
        )


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    block_no: int
    line_no: int
    word_no: int
    page: int

    @property
    def bbox(self) -> BBox:
        return BBox(self.x0, self.y0, self.x1, self.y1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "block_no": self.block_no,
            "line_no": self.line_no,
            "word_no": self.word_no,
            "page": self.page,
        }


@dataclass
class Span:
    text: str
    bbox: BBox
    font: str
    font_size: float
    flags: int
    color: int
    block_no: int
    line_no: int
    page: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "font": self.font,
            "font_size": self.font_size,
            "flags": self.flags,
            "color": self.color,
            "block_no": self.block_no,
            "line_no": self.line_no,
            "page": self.page,
        }


@dataclass
class TextBlock:
    block_no: int
    page: int
    bbox: BBox
    lines: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_no": self.block_no,
            "page": self.page,
            "bbox": self.bbox.to_dict(),
            "lines": self.lines,
        }


@dataclass
class Entity:
    id: str
    type: str
    subtype: str | None
    tag: str | None
    label: str | None
    page: int
    bbox: BBox | None
    center: tuple[float, float] | None
    confidence: float
    source: list[str]
    status: str = "detected"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "subtype": self.subtype,
            "tag": self.tag,
            "label": self.label,
            "page": self.page,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "center": list(self.center) if self.center else None,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class Node:
    id: str
    entity_id: str | None
    type: str
    tag: str | None
    label: str | None
    page: int
    bbox: BBox | None
    center: tuple[float, float] | None
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "type": self.type,
            "tag": self.tag,
            "label": self.label,
            "page": self.page,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "center": list(self.center) if self.center else None,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class Edge:
    id: str
    source: str
    target: str
    relationship: str
    line_tag: str | None
    direction: str | None
    page: int | None
    confidence: float
    status: str = "detected"
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "line_tag": self.line_tag,
            "direction": self.direction,
            "page": self.page,
            "confidence": round(self.confidence, 3),
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass
class LineSegment:
    id: str
    tag: str | None
    page: int
    points: list[tuple[float, float]]
    bbox: BBox | None
    confidence: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tag": self.tag,
            "page": self.page,
            "points": [list(p) for p in self.points],
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "confidence": round(self.confidence, 3),
            "source": self.source,
        }


@dataclass
class PageResult:
    page_number: int
    width: float
    height: float
    words: list[Word] = field(default_factory=list)
    blocks: list[TextBlock] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    lines: list[LineSegment] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    rendered_path: str | None = None
    has_text_layer: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "text": {
                "words": [w.to_dict() for w in self.words],
                "blocks": [b.to_dict() for b in self.blocks],
            },
            "entities": [e.to_dict() for e in self.entities],
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "lines": [l.to_dict() for l in self.lines],
            "annotations": self.annotations,
            "rendered_path": self.rendered_path,
            "has_text_layer": self.has_text_layer,
        }


@dataclass
class ExtractionResult:
    document: dict[str, Any]
    pages: list[PageResult] = field(default_factory=list)
    global_entities: list[Entity] = field(default_factory=list)
    global_connections: list[Edge] = field(default_factory=list)
    uncertain_items: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document,
            "pages": [p.to_dict() for p in self.pages],
            "global_entities": [e.to_dict() for e in self.global_entities],
            "global_connections": [e.to_dict() for e in self.global_connections],
            "uncertain_items": self.uncertain_items,
            "validation": self.validation,
        }

    def to_graph(self) -> dict[str, Any]:
        nodes = []
        edges = []
        seen_nodes: set[str] = set()
        for page in self.pages:
            for node in page.nodes:
                if node.id not in seen_nodes:
                    nodes.append(node.to_dict())
                    seen_nodes.add(node.id)
            edges.extend(e.to_dict() for e in page.edges)
        for node_entity in self.global_entities:
            nid = node_entity.id
            if nid not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": node_entity.type,
                    "tag": node_entity.tag,
                    "label": node_entity.label,
                    "page": node_entity.page,
                    "confidence": node_entity.confidence,
                })
                seen_nodes.add(nid)
        edges.extend(e.to_dict() for e in self.global_connections)
        return {"nodes": nodes, "edges": edges}
