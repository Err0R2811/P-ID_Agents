"""Visual analysis of rendered pages and vector drawings."""

from __future__ import annotations

import uuid
from typing import Any

from pid_extractor.config import LOW_CONFIDENCE, MEDIUM_CONFIDENCE, PipelineConfig
from pid_extractor.models import BBox, Entity, LineSegment


def _line_id() -> str:
    return f"line_{uuid.uuid4().hex[:12]}"


class VisualAnalyzer:
    """Analyze vector drawings and rendered pages for symbols and lines."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()

    def extract_line_segments(
        self,
        drawing_paths: list[list[tuple[float, float]]],
        page: int,
    ) -> list[LineSegment]:
        """Convert drawing paths to line segments."""
        segments: list[LineSegment] = []

        for points in drawing_paths:
            if len(points) < 2:
                continue

            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            bbox = BBox(
                x0=min(x_coords), y0=min(y_coords),
                x1=max(x_coords), y1=max(y_coords),
            )

            # Filter out very small paths (likely text decorations)
            if bbox.width < 2 and bbox.height < 2:
                continue

            segments.append(LineSegment(
                id=_line_id(),
                tag=None,
                page=page,
                points=points,
                bbox=bbox,
                confidence=LOW_CONFIDENCE,
                source="visual",
            ))

        return segments

    def detect_arrow_candidates(
        self,
        drawing_paths: list[list[tuple[float, float]]],
        page: int,
    ) -> list[dict[str, Any]]:
        """Identify potential flow direction arrows from small triangular paths."""
        arrows: list[dict[str, Any]] = []

        for points in drawing_paths:
            if len(points) != 3:
                continue
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)

            if 3 < width < 30 and 3 < height < 30:
                cx = sum(x_coords) / 3
                cy = sum(y_coords) / 3
                arrows.append({
                    "page": page,
                    "center": [cx, cy],
                    "points": [list(p) for p in points],
                    "confidence": LOW_CONFIDENCE,
                    "type": "arrow_candidate",
                    "status": "uncertain",
                })

        return arrows

    def associate_tags_with_symbols(
        self,
        entities: list[Entity],
        line_segments: list[LineSegment],
        page: int,
    ) -> list[Entity]:
        """Associate text tags with nearby visual elements."""
        updated: list[Entity] = []

        for entity in entities:
            if entity.bbox is None or entity.center is None:
                updated.append(entity)
                continue

            nearby_lines = self._find_nearby_lines(entity, line_segments)
            if nearby_lines:
                entity.source = list(set(entity.source + ["visual"]))
                entity.metadata["nearby_line_count"] = len(nearby_lines)
                if entity.confidence < MEDIUM_CONFIDENCE:
                    entity.confidence = min(entity.confidence + 0.1, 0.85)

            updated.append(entity)

        return updated

    def _find_nearby_lines(
        self,
        entity: Entity,
        lines: list[LineSegment],
        threshold: float | None = None,
    ) -> list[LineSegment]:
        threshold = threshold or self.config.proximity_threshold
        if entity.center is None:
            return []

        cx, cy = entity.center
        nearby: list[LineSegment] = []

        for line in lines:
            if line.bbox is None:
                continue
            lx, ly = line.bbox.center
            dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
            if dist <= threshold:
                nearby.append(line)

        return nearby

    def build_visual_entities_from_drawings(
        self,
        drawings: list[dict[str, Any]],
        page: int,
    ) -> list[Entity]:
        """Create placeholder entities for significant drawing regions."""
        entities: list[Entity] = []

        for drawing in drawings:
            rect = drawing.get("rect")
            if not rect:
                continue
            bbox = BBox.from_rect(tuple(rect))
            # Significant symbol-sized regions
            if 10 < bbox.width < 200 and 10 < bbox.height < 200:
                entities.append(Entity(
                    id=f"vis_{uuid.uuid4().hex[:12]}",
                    type="process_object",
                    subtype="symbol",
                    tag=None,
                    label=None,
                    page=page,
                    bbox=bbox,
                    center=bbox.center,
                    confidence=LOW_CONFIDENCE,
                    source=["visual"],
                    status="uncertain",
                    metadata={"drawing_index": drawing.get("index")},
                ))

        return entities
