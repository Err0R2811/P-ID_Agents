"""Asynchronous LLM client and prompt builders."""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path

import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings
from .exceptions import LLMCallError
from .logger import get_logger
from .models import ExtractedWord, PIDConnection

logger = get_logger(__name__)


RETRY_EXCEPTIONS = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.InternalServerError,
)


def _encode_image(path: Path) -> str:
    """Return a base64 data URL for a PNG image."""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _words_table(words: list[ExtractedWord]) -> str:
    """Format the extracted word list as a Markdown table."""
    lines = [
        "| text | x0 | y0 | x1 | y1 | split | overlap |",
        "|------|----|----|----|----|-------|---------|",
    ]
    for w in words:
        x0, y0, x1, y1 = w.source_rect()
        split = ",".join(str(s + 1) for s in w.splits)
        overlap = "yes" if w.in_overlap else "no"
        # Escape pipe characters in text
        text = w.text.replace("|", "\\|")
        lines.append(
            f"| {text} | {x0:.2f} | {y0:.2f} | {x1:.2f} | {y1:.2f} | {split} | {overlap} |"
        )
    return "\n".join(lines)


def _build_markdown_messages(
    image_paths: list[Path],
    words: list[ExtractedWord],
) -> list[dict]:
    text = (
        "You are an expert P&ID (Piping and Instrumentation Diagram) analyst.\n\n"
        "I am giving you three overlapping vertical sections of the same P&ID "
        "sheet (page 1) plus a list of extracted text with bounding boxes.\n\n"
        "Your task:\n"
        "- Produce a clear, well-structured Markdown summary of the P&ID.\n"
        "- Include:\n"
        "  - Document / sheet metadata if visible\n"
        "  - Equipment list (tag, description, type)\n"
        "  - Instrument list (tag, description, type)\n"
        "  - Line list (line number, service, size/spec if visible)\n"
        "  - Notable manifolds, junctions, or process notes\n"
        "  - Overall layout / flow orientation\n"
        "- Do not invent information not visible in the drawings or text.\n"
        "- Use the extracted word list for exact tag numbers and labels.\n\n"
        "The images are labeled part 1 (left), part 2 (middle), and part 3 (right). "
        "They overlap, so some equipment appears in two adjacent images.\n\n"
        "Extracted words with coordinates (source page coordinate system):\n\n"
        f"{_words_table(words)}"
    )

    content: list[dict] = [{"type": "text", "text": text}]
    for i, path in enumerate(image_paths, start=1):
        content.append({"type": "text", "text": f"--- Part {i} ---"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": _encode_image(path), "detail": "high"},
            }
        )

    return [{"role": "user", "content": content}]


def _build_json_messages(
    image_paths: list[Path],
    words: list[ExtractedWord],
) -> list[dict]:
    text = (
        "You are an expert P&ID (Piping and Instrumentation Diagram) analyst.\n\n"
        "I am giving you three overlapping vertical sections of the same P&ID "
        "sheet (page 1) plus a list of extracted text with bounding boxes.\n\n"
        "Your task:\n"
        "- Produce a JSON array of connections between equipment, instruments, and lines.\n"
        "- Each connection must include:\n"
        "  - source_tag (required): equipment or instrument tag at one end of the line\n"
        "  - source_name (optional): human-readable name/description\n"
        "  - target_tag (required): equipment or instrument tag at the other end\n"
        "  - target_name (optional): human-readable name/description\n"
        "  - line_number (optional): the line number/label shown on the connecting line\n"
        "  - line_type (optional): e.g. process, utility, instrument air, drain, vent\n"
        "  - connection_type (optional): e.g. flange, weld, thread, valve, tee\n"
        "  - bbox (optional): {x0, y0, x1, y1} in the original page coordinate system\n"
        "  - notes (optional): any other observations\n"
        "- Output ONLY a valid JSON array, no Markdown, no explanation, no code fences.\n"
        "- If a line connects equipment to an instrument, use the appropriate tags.\n"
        "- If a line connects to another line (manifold/tee), create a connection for each logical branch.\n"
        "- Do not invent tags; use the tags visible in the drawing or in the extracted word list.\n\n"
        "The images are labeled part 1 (left), part 2 (middle), and part 3 (right). "
        "They overlap, so some equipment appears in two adjacent images.\n\n"
        "Extracted words with coordinates (source page coordinate system):\n\n"
        f"{_words_table(words)}\n\n"
        "Return exactly one JSON array."
    )

    content: list[dict] = [{"type": "text", "text": text}]
    for i, path in enumerate(image_paths, start=1):
        content.append({"type": "text", "text": f"--- Part {i} ---"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": _encode_image(path), "detail": "high"},
            }
        )

    return [{"role": "user", "content": content}]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    reraise=True,
)
async def _call_openai(
    client: openai.AsyncOpenAI,
    messages: list[dict],
    settings: Settings,
) -> str:
    response = await client.chat.completions.create(
        model=settings.model,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=settings.llm_max_tokens,
        timeout=settings.request_timeout,
    )
    return response.choices[0].message.content or ""


def _clean_json(text: str) -> str:
    """Remove Markdown code fences and extra whitespace from a JSON response."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first code fence line and trailing fence
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_json(text: str) -> list[PIDConnection]:
    """Parse the cleaned JSON text into a list of PIDConnection models."""
    cleaned = _clean_json(text)
    if not cleaned:
        raise LLMCallError("LLM returned empty JSON response")

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMCallError(f"Could not parse JSON: {exc}") from exc

    if not isinstance(data, list):
        raise LLMCallError(f"Expected JSON array, got {type(data).__name__}")

    connections: list[PIDConnection] = []
    for i, item in enumerate(data):
        try:
            connections.append(PIDConnection.model_validate(item))
        except Exception as exc:
            logger.warning("Connection %s failed validation: %s", i, exc)
            # Continue with valid connections rather than failing the whole call

    return connections


async def _generate_markdown(
    image_paths: list[Path],
    words: list[ExtractedWord],
    client: openai.AsyncOpenAI,
    settings: Settings,
) -> str:
    messages = _build_markdown_messages(image_paths, words)
    logger.info("Calling LLM for Markdown (model=%s)", settings.model)
    try:
        return await _call_openai(client, messages, settings)
    except Exception as exc:
        raise LLMCallError(f"Markdown LLM call failed: {exc}") from exc


async def _generate_json(
    image_paths: list[Path],
    words: list[ExtractedWord],
    client: openai.AsyncOpenAI,
    settings: Settings,
) -> list[PIDConnection]:
    messages = _build_json_messages(image_paths, words)
    logger.info("Calling LLM for JSON (model=%s)", settings.model)
    try:
        text = await _call_openai(client, messages, settings)
    except Exception as exc:
        raise LLMCallError(f"JSON LLM call failed: {exc}") from exc

    return _parse_json(text)


async def run_llm_calls(
    image_paths: list[Path],
    words: list[ExtractedWord],
    settings: Settings,
) -> tuple[str, list[PIDConnection]]:
    """Run the Markdown and JSON LLM calls in parallel.

    Returns (markdown_text, connections).
    """
    if not settings.openai_api_key:
        raise LLMCallError(
            "OPENAI_API_KEY is not set. Provide it as an environment variable "
            "or in a .env file."
        )

    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.base_url,
    )

    markdown_task = _generate_markdown(image_paths, words, client, settings)
    json_task = _generate_json(image_paths, words, client, settings)

    try:
        markdown, connections = await asyncio.gather(
            markdown_task, json_task, return_exceptions=False
        )
    except Exception as exc:
        # If one fails, the other result is lost because gather raises the first
        # exception. Try to provide partial results by calling individually.
        logger.error("Parallel LLM call failed: %s", exc)
        raise

    return markdown, connections


async def run_llm_calls_with_partial(
    image_paths: list[Path],
    words: list[ExtractedWord],
    settings: Settings,
) -> tuple[str | None, list[PIDConnection] | None]:
    """Run LLM calls in parallel and return whatever succeeds.

    Useful for graceful degradation: if one call fails, the other result is
    still returned.
    """
    if not settings.openai_api_key:
        raise LLMCallError(
            "OPENAI_API_KEY is not set. Provide it as an environment variable "
            "or in a .env file."
        )

    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.base_url,
    )

    results = await asyncio.gather(
        _generate_markdown(image_paths, words, client, settings),
        _generate_json(image_paths, words, client, settings),
        return_exceptions=True,
    )

    markdown: str | None = None
    connections: list[PIDConnection] | None = None

    if isinstance(results[0], str):
        markdown = results[0]
    else:
        logger.error("Markdown LLM call failed: %s", results[0])

    if isinstance(results[1], list):
        connections = results[1]
    else:
        logger.error("JSON LLM call failed: %s", results[1])

    return markdown, connections
