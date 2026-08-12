"""Output formatting for SUMMARY, STRUCTURED, and GRAPH modes."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pid_extractor.models import ExtractionResult


class OutputFormatter:
    """Format extraction results for different output modes."""

    def format(self, result: ExtractionResult, mode: str) -> str:
        mode = mode.upper()
        if mode == "SUMMARY":
            return self.format_summary(result)
        if mode == "GRAPH":
            return json.dumps(result.to_graph(), indent=2, ensure_ascii=False)
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

    def save(self, result: ExtractionResult, path: str | Path, mode: str = "STRUCTURED") -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.format(result, mode)
        path.write_text(content, encoding="utf-8")
        return path

    def format_summary(self, result: ExtractionResult) -> str:
        lines: list[str] = []
        doc = result.document

        lines.append("=" * 60)
        lines.append("P&ID EXTRACTION SUMMARY")
        lines.append("=" * 60)
        lines.append(f"File:       {doc.get('filename', 'unknown')}")
        lines.append(f"Pages:      {doc.get('page_count', 0)}")
        lines.append(f"Processed:  {doc.get('pages_processed', 0)}")
        lines.append("")

        # Entity counts
        type_counts = Counter(e.type for e in result.global_entities)
        lines.append("ENTITY COUNTS")
        lines.append("-" * 40)
        for etype, count in sorted(type_counts.items()):
            lines.append(f"  {etype:20s} {count}")
        lines.append(f"  {'TOTAL':20s} {len(result.global_entities)}")
        lines.append("")

        # Tags by category
        equipment = [e for e in result.global_entities if e.type == "equipment" and e.tag]
        instruments = [e for e in result.global_entities if e.type == "instrument" and e.tag]
        valves = [e for e in result.global_entities if e.type == "valve" and e.tag]
        pipe_lines = [e for e in result.global_entities if e.type == "line" and e.tag]

        if equipment:
            lines.append("EQUIPMENT TAGS")
            lines.append("-" * 40)
            for e in sorted(equipment, key=lambda x: x.tag or ""):
                conf = f"{e.confidence:.2f}"
                lines.append(f"  {e.tag:15s} [{e.subtype or 'unknown':15s}] conf={conf} p.{e.page}")
            lines.append("")

        if instruments:
            lines.append("INSTRUMENT TAGS")
            lines.append("-" * 40)
            for e in sorted(instruments, key=lambda x: x.tag or ""):
                conf = f"{e.confidence:.2f}"
                lines.append(f"  {e.tag:15s} [{e.subtype or 'unknown':15s}] conf={conf} p.{e.page}")
            lines.append("")

        if valves:
            lines.append("VALVE TAGS")
            lines.append("-" * 40)
            for e in sorted(valves, key=lambda x: x.tag or ""):
                conf = f"{e.confidence:.2f}"
                lines.append(f"  {e.tag:15s} [{e.subtype or 'unknown':15s}] conf={conf} p.{e.page}")
            lines.append("")

        if pipe_lines:
            lines.append("LINE NUMBERS")
            lines.append("-" * 40)
            for e in sorted(pipe_lines, key=lambda x: x.tag or ""):
                lines.append(f"  {e.tag:20s} p.{e.page}")
            lines.append("")

        # Graph stats
        total_nodes = sum(len(p.nodes) for p in result.pages)
        total_edges = sum(len(p.edges) for p in result.pages) + len(result.global_connections)
        lines.append("GRAPH")
        lines.append("-" * 40)
        lines.append(f"  Nodes:              {total_nodes}")
        lines.append(f"  Edges (page):       {sum(len(p.edges) for p in result.pages)}")
        lines.append(f"  Edges (cross-page): {len(result.global_connections)}")
        lines.append(f"  Total edges:        {total_edges}")
        lines.append("")

        # Uncertain items
        if result.uncertain_items:
            lines.append(f"UNCERTAIN ITEMS ({len(result.uncertain_items)})")
            lines.append("-" * 40)
            for item in result.uncertain_items[:20]:
                tag = item.get("tag", item.get("id", "?"))
                lines.append(f"  [{item.get('type')}] {tag} conf={item.get('confidence', '?')} p.{item.get('page', '?')}")
            if len(result.uncertain_items) > 20:
                lines.append(f"  ... and {len(result.uncertain_items) - 20} more")
            lines.append("")

        # Validation
        validation = result.validation
        if validation:
            lines.append("VALIDATION")
            lines.append("-" * 40)
            lines.append(f"  Valid:    {validation.get('valid', True)}")
            lines.append(f"  Warnings: {validation.get('warning_count', 0)}")
            for w in validation.get("warnings", [])[:10]:
                lines.append(f"    [{w.get('code')}] {w.get('message')}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def lookup_tag(self, result: ExtractionResult, tag: str) -> dict[str, Any]:
        tag_upper = tag.upper()
        matches = [e for e in result.global_entities if e.tag and e.tag.upper() == tag_upper]

        related_edges = []
        node_ids = set()
        for page in result.pages:
            for node in page.nodes:
                if node.tag and node.tag.upper() == tag_upper:
                    node_ids.add(node.id)
            for edge in page.edges:
                if edge.source in node_ids or edge.target in node_ids:
                    related_edges.append(edge.to_dict())

        for edge in result.global_connections:
            if edge.source in node_ids or edge.target in node_ids:
                related_edges.append(edge.to_dict())

        return {
            "tag": tag_upper,
            "matches": [m.to_dict() for m in matches],
            "related_edges": related_edges,
            "match_count": len(matches),
        }

    def list_tags(self, result: ExtractionResult) -> dict[str, list[str]]:
        tags: dict[str, list[str]] = {
            "equipment": [],
            "instrument": [],
            "valve": [],
            "line": [],
            "other": [],
        }
        for entity in result.global_entities:
            if not entity.tag:
                continue
            category = entity.type if entity.type in tags else "other"
            if entity.tag not in tags[category]:
                tags[category].append(entity.tag)

        for key in tags:
            tags[key].sort()

        return tags
