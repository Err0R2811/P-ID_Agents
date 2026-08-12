"""Spatial reasoning for P&ID elements."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pid_extractor.config import PipelineConfig
from pid_extractor.models import BBox, Entity


@dataclass
class SpatialRelation:
    entity_a_id: str
    entity_b_id: str
    relation_type: str
    distance: float
    confidence: float
    evidence: list[str]


class SpatialReasoner:
    """Compute spatial relationships between entities.

    CRITICAL: Proximity alone does NOT imply semantic connection.
    All relations include confidence and require corroborating evidence.
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()

    def distance(self, a: Entity, b: Entity) -> float | None:
        if a.center is None or b.center is None:
            return None
        ax, ay = a.center
        bx, by = b.center
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

    def is_aligned_horizontally(
        self, a: Entity, b: Entity, tolerance: float | None = None
    ) -> bool:
        tolerance = tolerance or self.config.alignment_tolerance
        if a.center is None or b.center is None:
            return False
        return abs(a.center[1] - b.center[1]) <= tolerance

    def is_aligned_vertically(
        self, a: Entity, b: Entity, tolerance: float | None = None
    ) -> bool:
        tolerance = tolerance or self.config.alignment_tolerance
        if a.center is None or b.center is None:
            return False
        return abs(a.center[0] - b.center[0]) <= tolerance

    def find_proximity_pairs(
        self,
        entities: list[Entity],
        threshold: float | None = None,
    ) -> list[SpatialRelation]:
        threshold = threshold or self.config.proximity_threshold
        relations: list[SpatialRelation] = []

        located = [e for e in entities if e.center is not None and e.tag]

        for i, a in enumerate(located):
            for b in located[i + 1:]:
                dist = self.distance(a, b)
                if dist is None or dist > threshold:
                    continue

                evidence = ["proximity"]
                confidence = max(0.1, 0.5 - (dist / threshold) * 0.3)

                # Alignment adds weak evidence only
                if self.is_aligned_horizontally(a, b):
                    evidence.append("horizontal_alignment")
                    confidence += 0.05
                if self.is_aligned_vertically(a, b):
                    evidence.append("vertical_alignment")
                    confidence += 0.05

                # Same tag prefix suggests related equipment/instrument
                if a.tag and b.tag:
                    prefix_a = a.tag.split("-")[0] if "-" in a.tag else a.tag[:2]
                    prefix_b = b.tag.split("-")[0] if "-" in b.tag else b.tag[:2]
                    if prefix_a == prefix_b:
                        evidence.append("same_prefix")
                        confidence += 0.05

                relations.append(SpatialRelation(
                    entity_a_id=a.id,
                    entity_b_id=b.id,
                    relation_type="nearby",
                    distance=dist,
                    confidence=min(confidence, 0.6),  # Cap — proximity alone is weak
                    evidence=evidence,
                ))

        return relations

    def find_tag_symbol_associations(
        self,
        text_entities: list[Entity],
        visual_entities: list[Entity],
        threshold: float | None = None,
    ) -> list[SpatialRelation]:
        """Associate text tags with nearby symbol regions."""
        threshold = threshold or self.config.association_threshold
        relations: list[SpatialRelation] = []

        tagged = [e for e in text_entities if e.tag and e.center]
        symbols = [e for e in visual_entities if e.type == "process_object"]

        for tag_entity in tagged:
            best_dist = float("inf")
            best_symbol: Entity | None = None

            for symbol in symbols:
                if symbol.center is None:
                    continue
                dist = self.distance(tag_entity, symbol)
                if dist is not None and dist < best_dist:
                    best_dist = dist
                    best_symbol = symbol

            if best_symbol and best_dist <= threshold:
                confidence = max(0.3, 0.7 - (best_dist / threshold) * 0.4)
                relations.append(SpatialRelation(
                    entity_a_id=tag_entity.id,
                    entity_b_id=best_symbol.id,
                    relation_type="tag_symbol_association",
                    distance=best_dist,
                    confidence=confidence,
                    evidence=["proximity", "tag_symbol_pair"],
                ))

        return relations

    def bbox_overlap(self, a: BBox, b: BBox) -> bool:
        return not (a.x1 < b.x0 or b.x1 < a.x0 or a.y1 < b.y0 or b.y1 < a.y0)
