"""Merge and deduplicate LLM outputs."""

from __future__ import annotations

from .logger import get_logger
from .models import PIDConnection

logger = get_logger(__name__)


def deduplicate_connections(connections: list[PIDConnection]) -> list[PIDConnection]:
    """Deduplicate connections by a stable fingerprint.

    Connections that share the same source tag, target tag, and line number
    are considered duplicates. The first occurrence is kept.
    """
    seen: set[str] = set()
    deduped: list[PIDConnection] = []

    for conn in connections:
        key = conn.fingerprint()
        if key in seen:
            logger.debug("Duplicate connection skipped: %s", key)
            continue
        seen.add(key)
        deduped.append(conn)

    if len(deduped) < len(connections):
        logger.info(
            "Deduplicated %s connections to %s unique",
            len(connections),
            len(deduped),
        )

    return deduped


def merge_connections(connections: list[PIDConnection]) -> list[PIDConnection]:
    """Merge and deduplicate a list of connections.

    Currently this performs deduplication. More advanced stitching of
    boundary-crossing lines can be added here if the LLM returns partial
    connections that need to be chained across split boundaries.
    """
    return deduplicate_connections(connections)


def merge_markdown(contents: list[str]) -> str:
    """Merge multiple Markdown outputs into one document.

    For the current pipeline there is only one Markdown output, so this
    primarily normalizes whitespace.
    """
    if not contents:
        return ""

    if len(contents) == 1:
        return contents[0].strip()

    # If multiple outputs are ever combined (e.g. multi-page), join with
    # page separators.
    parts = [c.strip() for c in contents if c.strip()]
    return "\n\n---\n\n".join(parts)
