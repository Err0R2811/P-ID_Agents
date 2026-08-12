"""Configuration and constants for P&ID extraction."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Pattern

from dotenv import load_dotenv

load_dotenv()

# Rendering
DEFAULT_DPI = 150
CACHE_RENDERED_PAGES = True

# Spatial thresholds (points; 72 pts = 1 inch)
PROXIMITY_THRESHOLD = 50.0
ASSOCIATION_THRESHOLD = 80.0
ALIGNMENT_TOLERANCE = 5.0

# Confidence thresholds
HIGH_CONFIDENCE = 0.9
MEDIUM_CONFIDENCE = 0.7
LOW_CONFIDENCE = 0.5
UNCERTAIN_THRESHOLD = 0.5

# Instrument type codes (ISA-style)
INSTRUMENT_CODES = frozenset({
    "PT", "PI", "TT", "TI", "FT", "FI", "LT", "LI",
    "FIC", "LIC", "PIC", "TIC", "AIC", "SIC", "ZIC",
    "PDI", "PDT", "AT", "AE", "WT", "WE",
})

# Valve type codes
VALVE_CODES = frozenset({
    "PSV", "PCV", "FCV", "LCV", "TCV", "XV", "MOV", "HV", "CV",
    "BV", "GV", "NRV", "CKV", "SDV", "BDV",
})

# Equipment prefix codes
EQUIPMENT_PREFIXES = frozenset({
    "P", "E", "V", "T", "TK", "HX", "R", "C", "K", "D", "F", "M",
    "PU", "CP", "HE", "VE", "TK", "DR", "COL",
})

# Equipment subtype mapping from prefix
EQUIPMENT_SUBTYPES: dict[str, str] = {
    "P": "pump",
    "PU": "pump",
    "CP": "compressor",
    "C": "compressor",
    "K": "compressor",
    "V": "vessel",
    "VE": "vessel",
    "T": "tank",
    "TK": "tank",
    "E": "heat_exchanger",
    "HX": "heat_exchanger",
    "HE": "heat_exchanger",
    "R": "reactor",
    "D": "drum",
    "F": "filter",
    "M": "mixer",
    "COL": "column",
    "DR": "drum",
}

# P&ID search terms for page.search_for()
SEARCH_TERMS: list[str] = sorted(
    set(INSTRUMENT_CODES) | set(VALVE_CODES) | {
        "P-", "E-", "V-", "T-", "TK-", "HX-", "R-",
        "PSV", "PCV", "FCV", "LCV", "TCV",
        "PT", "PI", "TT", "TI", "FT", "FI", "LT", "LI",
        "FIC", "LIC", "PIC", "TIC", "XV", "MOV", "HV", "CV",
    }
)

# Regex patterns for tag detection
TAG_PATTERNS: list[tuple[str, Pattern[str]]] = [
    ("equipment", re.compile(
        r"\b(" + "|".join(EQUIPMENT_PREFIXES) + r")-(\d{2,5}[A-Z]?)\b", re.IGNORECASE
    )),
    ("instrument", re.compile(
        r"\b(" + "|".join(INSTRUMENT_CODES) + r")-(\d{2,5}[A-Z]?)\b", re.IGNORECASE
    )),
    ("valve", re.compile(
        r"\b(" + "|".join(VALVE_CODES) + r")-(\d{2,5}[A-Z]?)\b", re.IGNORECASE
    )),
    ("line", re.compile(
        r"\b(\d{1,2}[-\"]\d{1,4}[-\"]\d{1,4}[-\"]\d{1,4})\b"
    )),
    ("line_alt", re.compile(
        r"\b(L-?\d{2,5}[A-Z]?|LN-?\d{2,5})\b", re.IGNORECASE
    )),
    ("note", re.compile(r"\bNOTE\s*[\d.:]*\b", re.IGNORECASE)),
    ("spec", re.compile(r"\b(SPEC|DESIGN|OPERATING)\s*[:=]", re.IGNORECASE)),
]


@dataclass
class LLMConfig:
    """External LLM API configuration (OpenAI-compatible)."""

    api_key: str | None = None
    base_url: str = "https://apihub.agnes-ai.com/v1"
    model: str = "agnes-2.5-flash"
    enabled: bool = True
    temperature: float = 0.1

    @classmethod
    def from_env(cls) -> LLMConfig:
        api_key = os.getenv("LLM_API_KEY")
        enabled_env = os.getenv("LLM_ENABLED", "true").lower()
        return cls(
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL", "https://apihub.agnes-ai.com/v1"),
            model=os.getenv("LLM_MODEL", "agnes-2.5-flash"),
            enabled=enabled_env in ("1", "true", "yes") and bool(api_key),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        )


@dataclass
class PipelineConfig:
    """Runtime configuration for the extraction pipeline."""

    dpi: int = DEFAULT_DPI
    cache_pages: bool = CACHE_RENDERED_PAGES
    proximity_threshold: float = PROXIMITY_THRESHOLD
    association_threshold: float = ASSOCIATION_THRESHOLD
    pages: list[int] | None = None  # 1-indexed; None = all pages
    output_dir: str = "output"
    enable_visual: bool = True
    enable_drawings: bool = True
    enable_llm: bool = True
    min_confidence: float = 0.0
    llm: LLMConfig = field(default_factory=LLMConfig.from_env)

    def page_filter(self, page_number: int) -> bool:
        if self.pages is None:
            return True
        return page_number in self.pages

    @property
    def llm_active(self) -> bool:
        return self.enable_llm and self.llm.enabled and bool(self.llm.api_key)
