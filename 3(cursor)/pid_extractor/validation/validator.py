"""Validate extraction results — flag issues, never silently correct."""

from __future__ import annotations

from pid_extractor.config import UNCERTAIN_THRESHOLD
from pid_extractor.models import Edge, Entity, ExtractionResult, Node, PageResult


class ResultValidator:
    """Validate P&ID extraction results and flag suspicious findings."""

    def validate(self, result: ExtractionResult) -> dict:
        warnings: list[dict] = []
        errors: list[dict] = []

        warnings.extend(self._check_duplicate_tags(result))
        warnings.extend(self._check_entities_without_location(result))
        warnings.extend(self._check_low_confidence(result))
        warnings.extend(self._check_impossible_connections(result))
        warnings.extend(self._check_disconnected_segments(result))
        warnings.extend(self._check_missing_text_layer(result))

        return {
            "valid": len(errors) == 0,
            "warning_count": len(warnings),
            "error_count": len(errors),
            "warnings": warnings,
            "errors": errors,
        }

    def collect_uncertain_items(self, result: ExtractionResult) -> list[dict]:
        uncertain: list[dict] = []

        for page in result.pages:
            for entity in page.entities:
                if entity.status == "uncertain" or entity.confidence < UNCERTAIN_THRESHOLD:
                    uncertain.append({
                        "type": "entity",
                        "id": entity.id,
                        "tag": entity.tag,
                        "page": entity.page,
                        "confidence": entity.confidence,
                        "status": entity.status,
                        "reason": "low_confidence" if entity.confidence < UNCERTAIN_THRESHOLD else entity.status,
                    })

            for edge in page.edges:
                if edge.status == "uncertain" or edge.confidence < UNCERTAIN_THRESHOLD:
                    uncertain.append({
                        "type": "edge",
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "page": edge.page,
                        "confidence": edge.confidence,
                        "status": edge.status,
                        "reason": "low_confidence",
                    })

        return uncertain

    def _check_duplicate_tags(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        tag_counts: dict[str, list[int]] = {}

        for entity in result.global_entities:
            if entity.tag:
                tag_counts.setdefault(entity.tag.upper(), []).append(entity.page)

        for tag, pages in tag_counts.items():
            unique_pages = set(pages)
            if len(pages) > len(unique_pages):
                warnings.append({
                    "code": "DUPLICATE_TAG",
                    "message": f"Tag {tag} appears multiple times on same page",
                    "tag": tag,
                    "pages": pages,
                })

        return warnings

    def _check_entities_without_location(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        for entity in result.global_entities:
            if entity.bbox is None and entity.tag:
                warnings.append({
                    "code": "NO_LOCATION",
                    "message": f"Entity {entity.tag} has no bounding box",
                    "entity_id": entity.id,
                    "tag": entity.tag,
                })
        return warnings

    def _check_low_confidence(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        count = sum(
            1 for e in result.global_entities
            if e.confidence < UNCERTAIN_THRESHOLD
        )
        if count > 0:
            warnings.append({
                "code": "LOW_CONFIDENCE_ENTITIES",
                "message": f"{count} entities below confidence threshold ({UNCERTAIN_THRESHOLD})",
                "count": count,
            })
        return warnings

    def _check_impossible_connections(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        for page in result.pages:
            for edge in page.edges:
                if edge.source == edge.target:
                    warnings.append({
                        "code": "SELF_LOOP",
                        "message": f"Edge {edge.id} connects node to itself",
                        "edge_id": edge.id,
                        "page": page.page_number,
                    })
        return warnings

    def _check_disconnected_segments(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        for page in result.pages:
            if len(page.lines) > 0 and len(page.edges) == 0 and len(page.nodes) > 1:
                warnings.append({
                    "code": "DISCONNECTED_SEGMENTS",
                    "message": f"Page {page.page_number} has {len(page.lines)} line segments but no edges",
                    "page": page.page_number,
                    "line_count": len(page.lines),
                })
        return warnings

    def _check_missing_text_layer(self, result: ExtractionResult) -> list[dict]:
        warnings = []
        for page in result.pages:
            if not page.has_text_layer:
                warnings.append({
                    "code": "NO_TEXT_LAYER",
                    "message": f"Page {page.page_number} has no extractable text — visual-only analysis",
                    "page": page.page_number,
                })
        return warnings
