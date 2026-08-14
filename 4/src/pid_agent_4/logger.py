"""Logging setup."""

from __future__ import annotations

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure root logging for the CLI."""
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger("pid_agent_4")
    root.setLevel(level)
    root.handlers = [handler]
