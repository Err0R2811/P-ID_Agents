"""LLM-based P&ID page analysis — merges with PyMuPDF extraction."""

from __future__ import annotations

import uuid
from typing import Any

from pid_extractor.config import (
    LOW_CONFIDENCE,
    MEDIUM_CONFIDENCE,
    UNCERTAIN_THRESHOLD,
    PipelineConfig,
)
from pid_extractor.llm.client import LLMClient
from pid_extractor.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from pid_extractor.models import BBox, Edge, Entity, Node, Word
from pid_extractor.pdf.search import SearchHit


def _entity_id() -> str:
    return f"llm_{uuid.uuid4().hex[:12]}"


def _edge_id() -> str:
    return f"llm_edge_{uuid.uuid4().hex[:12]}"


class PIDLLMAnalyzer:
    """Use an external LLM to interpret rendered P&ID pages."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self._client: LLMClient | None = None

    @property
    def client(self) -> LLMClient:
        if self._client is None:
            llm = self.config.llm
            self._client = LLMClient(
                api_key=llm.api_key or "",
                base_url=llm.base_url,
                model=llm.model,
            )
        return self._client

    def analyze_page(
        self,
        image_path: str,
        page_number: int,
        width: float,
        height: float,
        words: list[Word],
        entities: list[Entity],
        search_hits: list[SearchHit],
    ) -> dict[str, Any]:
        """Run LLM vision analysis on a rendered page."""
        tags = sorted({e.tag for e in entities if e.tag})
        words_sample = " | ".join(
            f"{w.text}@{w.x0:.0f},{w.y0:.0f}" for w in words[:100]
        )
        hits_text = ", ".join(
            f"{h.term}@{h.bbox.x0:.0f},{h.bbox.y0:.0f}" for h in search_hits[:50]
        )

        user_prompt = build_user_prompt(
            page_number, width, height, tags, words_sample, hits_text
        )
        return self.client.analyze_image(image_path, SYSTEM_PROMPT, user_prompt)

    def merge_entities(
        self,
        existing: list[Entity],
        llm_result: dict[str, Any],
        page: int,
        page_width: float,
        page_height: float,
    ) -> list[Entity]:
        """Merge LLM-detected entities with PyMuPDF entities."""
        by_tag = {e.tag.upper(): e for e in existing if e.tag}
        merged = list(existing)

        for item in llm_result.get("entities", []):
            tag = item.get("tag")
            confidence = float(item.get("confidence", LOW_CONFIDENCE))
            status = item.get("status", "uncertain" if confidence < UNCERTAIN_THRESHOLD else "detected")
            bbox = self._parse_bbox(item.get("bbox"), page_width, page_height)

            if tag:
                key = tag.upper()
                if key in by_tag:
                    entity = by_tag[key]
                    entity.source = list(set(entity.source + ["llm"] + item.get("evidence", [])))
                    if confidence > entity.confidence:
                        entity.confidence = min(confidence, 0.98)
                    if item.get("subtype") and not entity.subtype:
                        entity.subtype = item["subtype"]
                    if bbox and entity.bbox is None:
                        entity.bbox = bbox
                        entity.center = bbox.center
                    if status == "detected" and entity.status == "uncertain":
                        entity.status = "detected"
                    continue

            merged.append(Entity(
                id=_entity_id(),
                type=item.get("type", "process_object"),
                subtype=item.get("subtype"),
                tag=tag,
                label=item.get("label"),
                page=page,
                bbox=bbox,
                center=bbox.center if bbox else None,
                confidence=confidence,
                source=["llm"] + item.get("evidence", ["visual"]),
                status=status,
                metadata={"llm_detected": True},
            ))
            if tag:
                by_tag[tag.upper()] = merged[-1]

        # Apply tag ↔ symbol associations
        for assoc in llm_result.get("associations", []):
            tag = assoc.get("tag")
            if not tag:
                continue
            entity = by_tag.get(tag.upper())
            if entity:
                entity.source = list(set(entity.source + ["llm", "visual"]))
                conf = float(assoc.get("confidence", MEDIUM_CONFIDENCE))
                entity.confidence = max(entity.confidence, min(conf, 0.95))
                if assoc.get("symbol_type") and not entity.subtype:
                    entity.subtype = assoc["symbol_type"]

        return merged

    def build_edges_from_llm(
        self,
        llm_result: dict[str, Any],
        nodes: list[Node],
        page: int,
    ) -> list[Edge]:
        """Convert LLM connection suggestions to Edge objects."""
        node_by_tag = {n.tag.upper(): n for n in nodes if n.tag}
        edges: list[Edge] = []

        for conn in llm_result.get("connections", []):
            src_tag = conn.get("source_tag")
            tgt_tag = conn.get("target_tag")
            if not src_tag or not tgt_tag:
                continue

            src_node = node_by_tag.get(src_tag.upper())
            tgt_node = node_by_tag.get(tgt_tag.upper())
            if not src_node or not tgt_node:
                continue

            confidence = float(conn.get("confidence", LOW_CONFIDENCE))
            status = conn.get("status", "uncertain" if confidence < UNCERTAIN_THRESHOLD else "detected")

            edges.append(Edge(
                id=_edge_id(),
                source=src_node.id,
                target=tgt_node.id,
                relationship=conn.get("relationship", "connected_to"),
                line_tag=conn.get("line_tag"),
                direction=conn.get("direction"),
                page=page,
                confidence=confidence,
                status=status,
                evidence=["llm"] + conn.get("evidence", []),
            ))

        return edges

    @staticmethod
    def _parse_bbox(
        raw: list[float] | None,
        page_width: float,
        page_height: float,
    ) -> BBox | None:
        if not raw or len(raw) != 4:
            return None
        x0, y0, x1, y1 = raw
        # Reject normalized 0-1 coords by scaling up
        if all(0 <= v <= 1 for v in raw):
            x0, y0, x1, y1 = x0 * page_width, y0 * page_height, x1 * page_width, y1 * page_height
        return BBox(x0, y0, x1, y1)
