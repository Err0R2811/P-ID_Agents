#!/usr/bin/env python3
"""CLI entry point for P&ID PDF extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pid_extractor.config import PipelineConfig
from pid_extractor.pipeline.processor import PIDProcessor
from pid_extractor.output.formatter import OutputFormatter


def cmd_extract(args: argparse.Namespace) -> int:
    config = PipelineConfig(
        dpi=args.dpi,
        pages=args.pages,
        output_dir=args.output_dir,
        enable_visual=not args.no_visual,
        enable_llm=not args.no_llm,
    )
    processor = PIDProcessor(config)
    output_path = args.output
    if not output_path:
        stem = Path(args.pdf).stem
        ext = "json" if args.mode.upper() != "SUMMARY" else "txt"
        output_path = str(Path(args.output_dir) / f"{stem}_{args.mode.lower()}.{ext}")

    result = processor.extract_and_save(args.pdf, output_path, args.mode)
    print(f"Extracted {len(result.global_entities)} entities from {result.document['pages_processed']} pages")
    if result.document.get("llm_enabled"):
        print(f"LLM analysis: {result.document.get('llm_model')}")
    else:
        print("LLM analysis: disabled (PyMuPDF heuristics only)")
    print(f"Output: {output_path}")
    if result.uncertain_items:
        print(f"Warning: {len(result.uncertain_items)} uncertain items flagged")
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    config = PipelineConfig(output_dir=args.output_dir, enable_llm=not args.no_llm)
    processor = PIDProcessor(config)
    result = processor.process(args.pdf)
    formatter = OutputFormatter()
    lookup = formatter.lookup_tag(result, args.tag)
    print(json.dumps(lookup, indent=2, ensure_ascii=False))
    return 0


def cmd_tags(args: argparse.Namespace) -> int:
    config = PipelineConfig(output_dir=args.output_dir, enable_llm=not args.no_llm)
    processor = PIDProcessor(config)
    result = processor.process(args.pdf)
    formatter = OutputFormatter()
    tags = formatter.list_tags(result)
    print(json.dumps(tags, indent=2, ensure_ascii=False))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    config = PipelineConfig(
        dpi=args.dpi,
        pages=args.pages,
        output_dir=args.output_dir,
        enable_llm=not args.no_llm,
    )
    processor = PIDProcessor(config)
    result = processor.process(args.pdf)
    formatter = OutputFormatter()
    print(formatter.format_summary(result))
    return 0


def cmd_flowchart(args: argparse.Namespace) -> int:
    """Generate process flowchart JPG and PDF from extraction JSON."""
    from generate_flowchart import draw_flowchart, load_entities

    stem = Path(args.pdf).stem
    out_dir = Path(args.output_dir)
    json_path = out_dir / f"{stem}_structured.json"
    if not json_path.exists():
        print(f"No extraction JSON found at {json_path}. Running extract first...")
        cmd_extract(argparse.Namespace(
            pdf=args.pdf, output=str(json_path), mode="structured",
            pages=args.pages, dpi=args.dpi, output_dir=args.output_dir,
            no_visual=False, no_llm=True,
        ))

    entities = load_entities(json_path)
    jpg_path = out_dir / f"{stem}_flowchart.jpg"
    pdf_path = out_dir / f"{stem}_flowchart.pdf"
    draw_flowchart(entities, jpg_path, pdf_path)
    print(f"Flowchart JPG: {jpg_path}")
    print(f"Flowchart PDF: {pdf_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P&ID PDF Extraction — Extract equipment, instruments, and connections from Piping & Instrumentation Diagrams",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = sub.add_parser("extract", help="Extract P&ID data from PDF")
    p_extract.add_argument("pdf", help="Path to P&ID PDF file")
    p_extract.add_argument("-o", "--output", help="Output file path")
    p_extract.add_argument(
        "--mode", choices=["summary", "structured", "graph"], default="structured",
        help="Output mode (default: structured)",
    )
    p_extract.add_argument("--pages", type=int, nargs="+", help="Specific pages to process (1-indexed)")
    p_extract.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")
    p_extract.add_argument("--output-dir", default="output", help="Output directory")
    p_extract.add_argument("--no-visual", action="store_true", help="Skip visual analysis")
    p_extract.add_argument("--no-llm", action="store_true", help="Skip LLM API analysis (PyMuPDF only)")
    p_extract.set_defaults(func=cmd_extract)

    # lookup
    p_lookup = sub.add_parser("lookup", help="Look up equipment/instrument by tag")
    p_lookup.add_argument("pdf", help="Path to P&ID PDF file")
    p_lookup.add_argument("--tag", required=True, help="Tag to look up (e.g., P-101)")
    p_lookup.add_argument("--output-dir", default="output")
    p_lookup.add_argument("--no-llm", action="store_true")
    p_lookup.set_defaults(func=cmd_lookup)

    # tags
    p_tags = sub.add_parser("tags", help="List all detected tags")
    p_tags.add_argument("pdf", help="Path to P&ID PDF file")
    p_tags.add_argument("--output-dir", default="output")
    p_tags.add_argument("--no-llm", action="store_true")
    p_tags.set_defaults(func=cmd_tags)

    # summary
    p_summary = sub.add_parser("summary", help="Print human-readable summary")
    p_summary.add_argument("pdf", help="Path to P&ID PDF file")
    p_summary.add_argument("--pages", type=int, nargs="+")
    p_summary.add_argument("--dpi", type=int, default=150)
    p_summary.add_argument("--output-dir", default="output")
    p_summary.add_argument("--no-llm", action="store_true")
    p_summary.set_defaults(func=cmd_summary)

    # flowchart
    p_flow = sub.add_parser("flowchart", help="Generate process flowchart (JPG + PDF)")
    p_flow.add_argument("pdf", help="Path to P&ID PDF file")
    p_flow.add_argument("--pages", type=int, nargs="+")
    p_flow.add_argument("--dpi", type=int, default=150)
    p_flow.add_argument("--output-dir", default="output")
    p_flow.set_defaults(func=cmd_flowchart)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not Path(args.pdf).exists():
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
