"""CLI entry point and pipeline orchestration."""

from __future__ import annotations

import argparse
import asyncio
import traceback
from pathlib import Path

import pymupdf

from .config import Settings
from .exceptions import PIDAgentError
from .extractor import extract_all_words
from .logger import configure_logging, get_logger
from .llm import run_llm_calls_with_partial
from .merger import merge_connections, merge_markdown
from .output import write_json, write_markdown
from .pdf import get_page_dimensions, open_pdf, validate_pdf
from .splitter import create_split_pdfs

logger = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pid-agent-4",
        description="Process a P&ID PDF into Markdown and JSON outputs.",
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the P&ID PDF file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output files (default: ./out)",
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=None,
        help="Overlap fraction between adjacent splits (default: 0.15)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=None,
        help="DPI for rendered split PNGs (default: 150)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="OpenAI model name (default: gpt-4o)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--splits-only",
        action="store_true",
        help="Only split and extract words; skip LLM calls",
    )
    return parser


def _merge_cli_settings(args: argparse.Namespace) -> Settings:
    """Build Settings, letting CLI args override environment/defaults."""
    overrides: dict = {}
    if args.output_dir is not None:
        overrides["output_dir"] = args.output_dir
    if args.overlap is not None:
        overrides["overlap"] = args.overlap
    if args.dpi is not None:
        overrides["dpi"] = args.dpi
    if args.model is not None:
        overrides["model"] = args.model
    if args.log_level is not None:
        overrides["log_level"] = args.log_level
    return Settings(**overrides)


async def _run_pipeline(settings: Settings, pdf_path: Path, splits_only: bool) -> None:
    """Run the full P&ID processing pipeline."""
    output_dir = settings.output_dir
    split_dir = settings.split_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    split_dir.mkdir(parents=True, exist_ok=True)

    doc = open_pdf(pdf_path)
    try:
        validate_pdf(doc, page_number=0)
    except PIDAgentError:
        doc.close()
        raise

    page_width, page_height = get_page_dimensions(doc, page_number=0)
    logger.info(
        "Processing page 1 of %s: %.2f x %.2f points",
        pdf_path,
        page_width,
        page_height,
    )

    boxes, pdf_paths, png_paths = create_split_pdfs(
        doc,
        split_dir,
        page_number=0,
        overlap=settings.overlap,
        split_count=settings.split_count,
        dpi=settings.dpi,
    )

    words = extract_all_words(
        doc,
        boxes,
        page_width=page_width,
        overlap=settings.overlap,
        page_number=0,
    )
    logger.info("Extracted %s unique words", len(words))

    if splits_only:
        logger.info("--splits-only set; skipping LLM calls")
        doc.close()
        return

    markdown, raw_connections = await run_llm_calls_with_partial(
        png_paths, words, settings
    )

    if markdown is None and raw_connections is None:
        raise PIDAgentError("Both LLM calls failed; no output produced")

    if markdown is not None:
        md_path = write_markdown(markdown, output_dir)
    else:
        logger.warning("Markdown LLM call failed; no .md file written")

    if raw_connections is not None:
        connections = merge_connections(raw_connections)
        json_path = write_json(connections, output_dir)
    else:
        logger.warning("JSON LLM call failed; no .json file written")
        connections = []

    doc.close()
    logger.info("Done. Outputs: %s, %s", md_path, json_path)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    settings = _merge_cli_settings(args)
    configure_logging(settings.log_level)

    try:
        asyncio.run(_run_pipeline(settings, args.pdf_path, args.splits_only))
    except PIDAgentError as exc:
        logger.error("Pipeline error: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        logger.debug(traceback.format_exc())
        return 1

    return 0
