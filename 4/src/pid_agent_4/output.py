"""Write final outputs to disk."""

from __future__ import annotations

import json
from pathlib import Path

from .logger import get_logger
from .models import PIDConnection

logger = get_logger(__name__)


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_markdown(content: str, output_dir: Path, filename: str = "output.md") -> Path:
    """Write Markdown content to the output directory."""
    path = Path(output_dir) / filename
    _ensure_dir(path)
    path.write_text(content, encoding="utf-8")
    logger.info("Wrote Markdown to %s", path)
    return path


def write_json(
    connections: list[PIDConnection],
    output_dir: Path,
    filename: str = "output.json",
) -> Path:
    """Write the JSON connection list to the output directory."""
    path = Path(output_dir) / filename
    _ensure_dir(path)

    data = [conn.model_dump(exclude_none=True) for conn in connections]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Wrote JSON to %s (%s connections)", path, len(connections))
    return path
