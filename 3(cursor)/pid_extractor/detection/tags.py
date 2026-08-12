"""Tag parsing for P&ID nomenclature."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pid_extractor.config import (
    EQUIPMENT_PREFIXES,
    EQUIPMENT_SUBTYPES,
    INSTRUMENT_CODES,
    TAG_PATTERNS,
    VALVE_CODES,
)


@dataclass
class ParsedTag:
    raw: str
    category: str
    prefix: str
    number: str
    full_tag: str
    subtype: str | None = None

    @property
    def is_equipment(self) -> bool:
        return self.category == "equipment"

    @property
    def is_instrument(self) -> bool:
        return self.category == "instrument"

    @property
    def is_valve(self) -> bool:
        return self.category == "valve"

    @property
    def is_line(self) -> bool:
        return self.category in ("line", "line_alt")


class TagParser:
    """Parse P&ID tags from text using regex patterns."""

    def parse_text(self, text: str) -> list[ParsedTag]:
        tags: list[ParsedTag] = []
        seen: set[str] = set()

        for category, pattern in TAG_PATTERNS:
            for match in pattern.finditer(text):
                full_tag = match.group(0).upper()
                if full_tag in seen:
                    continue
                seen.add(full_tag)

                if category in ("line", "line_alt", "note", "spec"):
                    tags.append(ParsedTag(
                        raw=match.group(0),
                        category=category,
                        prefix=category,
                        number=match.group(1) if match.lastindex else "",
                        full_tag=full_tag,
                    ))
                else:
                    prefix = match.group(1).upper()
                    number = match.group(2)
                    subtype = self._resolve_subtype(category, prefix)
                    tags.append(ParsedTag(
                        raw=match.group(0),
                        category=category,
                        prefix=prefix,
                        number=number,
                        full_tag=full_tag,
                        subtype=subtype,
                    ))

        return tags

    def parse_words(self, words: list) -> list[ParsedTag]:
        """Parse tags from concatenated word text and individual words."""
        all_tags: list[ParsedTag] = []
        seen: set[str] = set()

        # Full page text
        full_text = " ".join(w.text for w in words)
        for tag in self.parse_text(full_text):
            if tag.full_tag not in seen:
                seen.add(tag.full_tag)
                all_tags.append(tag)

        # Individual words (handles split tags)
        for word in words:
            for tag in self.parse_text(word.text):
                if tag.full_tag not in seen:
                    seen.add(tag.full_tag)
                    all_tags.append(tag)

        return all_tags

    def classify_prefix(self, prefix: str) -> str:
        prefix = prefix.upper()
        if prefix in INSTRUMENT_CODES:
            return "instrument"
        if prefix in VALVE_CODES:
            return "valve"
        if prefix in EQUIPMENT_PREFIXES:
            return "equipment"
        return "unknown"

    def _resolve_subtype(self, category: str, prefix: str) -> str | None:
        prefix = prefix.upper()
        if category == "equipment":
            return EQUIPMENT_SUBTYPES.get(prefix, "equipment")
        if category == "instrument":
            if prefix.endswith("IC"):
                return "controller"
            if prefix.endswith("T"):
                return "transmitter"
            if prefix.endswith("I"):
                return "indicator"
            return "instrument"
        if category == "valve":
            valve_subtypes = {
                "PSV": "pressure_safety", "PCV": "pressure_control",
                "FCV": "flow_control", "LCV": "level_control",
                "TCV": "temperature_control", "XV": "on_off",
                "MOV": "motor_operated", "HV": "hand_valve",
                "CV": "control_valve", "NRV": "check_valve",
            }
            return valve_subtypes.get(prefix, "valve")
        return None
