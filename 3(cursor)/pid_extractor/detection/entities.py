"""Entity detection from text, layout, and search hits."""

from __future__ import annotations

import uuid
from typing import Any

from pid_extractor.config import (
    LOW_CONFIDENCE,
    MEDIUM_CONFIDENCE,
    HIGH_CONFIDENCE,
    UNCERTAIN_THRESHOLD,
    PipelineConfig,
)
from pid_extractor.detection.tags import ParsedTag, TagParser
from pid_extractor.models import BBox, Entity, Word
from pid_extractor.pdf.search import SearchHit


def _entity_id() -> str:
    return f"ent_{uuid.uuid4().hex[:12]}"


class EntityDetector:
    """Detect P&ID entities from extracted text and search results."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.tag_parser = TagParser()

    def detect_from_words(
        self,
        words: list[Word],
        page: int,
    ) -> list[Entity]:
        entities: list[Entity] = []
        parsed_tags = self.tag_parser.parse_words(words)

        for tag in parsed_tags:
            bbox, confidence, sources = self._locate_tag(words, tag, page)
            status = "detected" if confidence >= UNCERTAIN_THRESHOLD else "uncertain"

            entities.append(Entity(
                id=_entity_id(),
                type=tag.category if tag.category not in ("line_alt",) else "line",
                subtype=tag.subtype,
                tag=tag.full_tag,
                label=tag.raw,
                page=page,
                bbox=bbox,
                center=bbox.center if bbox else None,
                confidence=confidence,
                source=sources,
                status=status,
                metadata={"prefix": tag.prefix, "number": tag.number},
            ))

        # Detect notes and specifications from text blocks
        entities.extend(self._detect_annotations(words, page))

        return entities

    def detect_from_search_hits(
        self,
        hits: list[SearchHit],
        existing_tags: set[str],
        page: int,
    ) -> list[Entity]:
        """Supplement entity detection with search_for results."""
        entities: list[Entity] = []
        for hit in hits:
            parsed = self.tag_parser.parse_text(hit.term)
            if not parsed:
                # Raw search term without full tag pattern
                if hit.term.upper() in existing_tags:
                    continue
                entities.append(Entity(
                    id=_entity_id(),
                    type="annotation",
                    subtype="search_hit",
                    tag=None,
                    label=hit.term,
                    page=page,
                    bbox=hit.bbox,
                    center=hit.bbox.center,
                    confidence=LOW_CONFIDENCE,
                    source=["text", "search"],
                    status="uncertain",
                    metadata={"context": hit.context},
                ))
                continue

            for tag in parsed:
                if tag.full_tag in existing_tags:
                    continue
                entities.append(Entity(
                    id=_entity_id(),
                    type=tag.category if tag.category not in ("line_alt",) else "line",
                    subtype=tag.subtype,
                    tag=tag.full_tag,
                    label=tag.raw,
                    page=page,
                    bbox=hit.bbox,
                    center=hit.bbox.center,
                    confidence=MEDIUM_CONFIDENCE,
                    source=["text", "search"],
                    status="detected",
                    metadata={"prefix": tag.prefix, "number": tag.number},
                ))

        return entities

    def _locate_tag(
        self,
        words: list[Word],
        tag: ParsedTag,
        page: int,
    ) -> tuple[BBox | None, float, list[str]]:
        """Find bbox for a parsed tag among words."""
        sources = ["text"]
        matching_words = []

        tag_upper = tag.full_tag.upper()
        tag_parts = tag.full_tag.replace("-", " ").upper().split()

        for word in words:
            word_upper = word.text.upper()
            if tag_upper in word_upper or word_upper in tag_upper:
                matching_words.append(word)
            elif all(part in word_upper for part in tag_parts if len(part) > 1):
                matching_words.append(word)

        if not matching_words:
            # Try adjacent word combination
            for i in range(len(words) - 1):
                combined = f"{words[i].text}-{words[i+1].text}".upper()
                if combined == tag_upper or tag_upper in combined:
                    matching_words = [words[i], words[i+1]]
                    break

        if matching_words:
            x0 = min(w.x0 for w in matching_words)
            y0 = min(w.y0 for w in matching_words)
            x1 = max(w.x1 for w in matching_words)
            y1 = max(w.y1 for w in matching_words)
            bbox = BBox(x0, y0, x1, y1)
            confidence = HIGH_CONFIDENCE if len(matching_words) >= 1 else MEDIUM_CONFIDENCE
            sources.append("layout")
            return bbox, confidence, sources

        return None, LOW_CONFIDENCE, sources

    def _detect_annotations(self, words: list[Word], page: int) -> list[Entity]:
        """Detect notes, specs, and unit labels."""
        entities: list[Entity] = []
        full_text = " ".join(w.text for w in words)

        note_keywords = ["NOTE", "NOTES", "REMARK", "COMMENT"]
        spec_keywords = ["DESIGN", "OPERATING", "SPEC", "MATL", "MATERIAL"]
        unit_patterns = ["PSIG", "PSIA", "DEG", "GPM", "BPD", "SCFM", "LB/HR", "KG/HR"]

        for word in words:
            upper = word.text.upper()
            if any(kw in upper for kw in note_keywords):
                entities.append(Entity(
                    id=_entity_id(),
                    type="annotation",
                    subtype="note",
                    tag=None,
                    label=word.text,
                    page=page,
                    bbox=word.bbox,
                    center=word.bbox.center,
                    confidence=MEDIUM_CONFIDENCE,
                    source=["text"],
                    status="detected",
                ))
            elif any(kw in upper for kw in spec_keywords):
                entities.append(Entity(
                    id=_entity_id(),
                    type="annotation",
                    subtype="specification",
                    tag=None,
                    label=word.text,
                    page=page,
                    bbox=word.bbox,
                    center=word.bbox.center,
                    confidence=MEDIUM_CONFIDENCE,
                    source=["text"],
                    status="detected",
                ))
            elif upper in unit_patterns:
                entities.append(Entity(
                    id=_entity_id(),
                    type="annotation",
                    subtype="unit",
                    tag=None,
                    label=word.text,
                    page=page,
                    bbox=word.bbox,
                    center=word.bbox.center,
                    confidence=HIGH_CONFIDENCE,
                    source=["text"],
                    status="detected",
                ))

        return entities

    def deduplicate(self, entities: list[Entity]) -> list[Entity]:
        """Remove duplicate entities by tag, keeping highest confidence."""
        by_tag: dict[str, Entity] = {}
        no_tag: list[Entity] = []

        for entity in entities:
            if entity.tag:
                key = f"{entity.tag}:{entity.page}"
                existing = by_tag.get(key)
                if existing is None or entity.confidence > existing.confidence:
                    by_tag[key] = entity
            else:
                no_tag.append(entity)

        return list(by_tag.values()) + no_tag
