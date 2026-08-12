#!/usr/bin/env python3
"""Run full P&ID extraction with Agnes LLM API and generate outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from pid_extractor.config import PipelineConfig
from pid_extractor.pipeline.processor import PIDProcessor


def main() -> int:
    pdf = ROOT / "123.pdf"
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    json_out = out_dir / "123_structured.json"
    summary_out = out_dir / "123_summary.txt"

    config = PipelineConfig(
        output_dir=str(out_dir),
        enable_llm=True,
        enable_visual=True,
        enable_drawings=True,
        dpi=150,
    )

    print(f"LLM active: {config.llm_active}")
    print(f"Base URL: {config.llm.base_url}")
    print(f"Model: {config.llm.model}")
    print(f"Processing: {pdf}")

    processor = PIDProcessor(config)
    result = processor.process(pdf)

    # Save structured JSON
    processor.formatter.save(result, json_out, "structured")
    print(f"Saved: {json_out}")

    # Save summary
    summary = processor.formatter.format_summary(result)
    summary_out.write_text(summary, encoding="utf-8")
    print(f"Saved: {summary_out}")

    # Generate flowchart
    try:
        from generate_flowchart import draw_flowchart, load_entities
        entities = result.global_entities
        entity_dicts = [e.to_dict() for e in entities]
        # load_entities expects JSON file format; build from result
        draw_flowchart(
            [{"tag": e.tag, "type": e.type, "subtype": e.subtype, "label": e.label}
             for e in result.global_entities],
            out_dir / "123_flowchart.jpg",
            out_dir / "123_flowchart.pdf",
        )
        print(f"Saved flowchart JPG/PDF")
    except Exception as exc:
        print(f"Flowchart generation skipped: {exc}")

    print(f"\nEntities: {len(result.global_entities)}")
    print(f"Connections: {len(result.global_connections)}")
    print(f"Uncertain: {len(result.uncertain_items)}")
    if result.document.get("llm_enabled"):
        print("LLM analysis: ENABLED")
    else:
        print("WARNING: LLM was not active")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
