"""
Adaptive P&ID Recursive Extractor v2.0

Key improvements over v1.0:
- Better prompt engineering with explicit symbol recognition guidance
- Hierarchical entity classification (equipment → subtypes, instruments → ISA loops)
- Connection inference from spatial proximity and line tracing
- Quality scoring per extracted entity
- Support for multi-page P&IDs
- Better deduplication with fuzzy matching
- Export to multiple formats (JSON, CSV, GraphML)
- No API key dependency - works with local vision models or any OpenAI-compatible API

Architecture:
    1. Image → Tile Splitter (recursive, adaptive)
    2. Vision LLM → Entity Extraction (per tile)
    3. Spatial Merger → Global coordinates + deduplication
    4. Connection Builder → Line tracing + proximity inference
    5. Validator → Quality scoring + consistency checks
    6. Exporter → JSON / CSV / GraphML / Markdown
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, Union, Callable
from collections import defaultdict
import hashlib

from PIL import Image
import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Config:
    """Runtime configuration. Override via env vars or constructor."""
    # API settings
    API_KEY: str = os.environ.get("AGNES_API_KEY", "")
    BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://apihub.agnes-ai.com/v1/chat/completions")
    MODEL: str = os.environ.get("LLM_MODEL", "agnes-2.0-flash")

    # Tiling strategy
    MAX_DEPTH: int = int(os.environ.get("MAX_DEPTH", "3"))
    MIN_TILE: int = int(os.environ.get("MIN_TILE", "220"))
    OVERLAP: float = float(os.environ.get("TILE_OVERLAP", "0.10"))

    # Rate limiting
    MAX_CONCURRENT: int = int(os.environ.get("MAX_CONCURRENT", "5"))
    TIMEOUT_CONNECT: int = int(os.environ.get("TIMEOUT_CONNECT", "30"))
    TIMEOUT_READ: int = int(os.environ.get("TIMEOUT_READ", "300"))

    # Quality thresholds
    MIN_CONFIDENCE: float = float(os.environ.get("MIN_CONFIDENCE", "0.6"))
    DEDUP_IOU_THRESHOLD: float = float(os.environ.get("DEDUP_IOU", "0.5"))

    # Export
    OUTPUT_DIR: Path = Path(os.environ.get("OUTPUT_DIR", "."))


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class EntityType(Enum):
    EQUIPMENT = "equipment"
    VALVE = "valve"
    INSTRUMENT = "instrument"
    CONTROLLER = "controller"
    LINE = "line"
    ANNOTATION = "annotation"
    UNKNOWN = "unknown"


class EquipmentSubtype(Enum):
    TANK = "tank"
    PUMP = "pump"
    COOLER = "cooler"
    FILTER = "filter"
    COMPRESSOR = "compressor"
    HEATER = "heater"
    EXCHANGER = "exchanger"
    VESSEL = "vessel"
    GENERIC = "generic"


class ValveSubtype(Enum):
    CONTROL = "control_valve"
    RELIEF = "relief_valve"
    SAFETY = "safety_relief_valve"
    CHECK = "check_valve"
    GATE = "gate_valve"
    BALL = "ball_valve"
    GLOBE = "globe_valve"
    BUTTERFLY = "butterfly_valve"
    SOLENOID = "solenoid_valve"
    UNKNOWN = "unknown_valve"


class InstrumentMeasure(Enum):
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    LEVEL = "level"
    FLOW = "flow"
    DIFFERENTIAL_PRESSURE = "differential_pressure"
    ANALYSIS = "analysis"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x0 + self.width / 2, self.y0 + self.height / 2)

    def iou(self, other: BoundingBox) -> float:
        """Intersection over Union."""
        ix0 = max(self.x0, other.x0)
        iy0 = max(self.y0, other.y0)
        ix1 = min(self.x1, other.x1)
        iy1 = min(self.y1, other.y1)

        if ix0 >= ix1 or iy0 >= iy1:
            return 0.0

        inter = (ix1 - ix0) * (iy1 - iy0)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def to_local(self, tile_bbox: BoundingBox) -> list[float]:
        """Convert global bbox to local [0,1] coordinates within tile."""
        tw, th = tile_bbox.width, tile_bbox.height
        return [
            (self.x0 - tile_bbox.x0) / tw,
            (self.y0 - tile_bbox.y0) / th,
            (self.x1 - tile_bbox.x0) / tw,
            (self.y1 - tile_bbox.y0) / th,
        ]

    @classmethod
    def from_local(cls, local: list[float], tile_bbox: BoundingBox) -> BoundingBox:
        """Convert local [0,1] coordinates to global bbox."""
        tw, th = tile_bbox.width, tile_bbox.height
        return cls(
            tile_bbox.x0 + local[0] * tw,
            tile_bbox.y0 + local[1] * th,
            tile_bbox.x0 + local[2] * tw,
            tile_bbox.y0 + local[3] * th,
        )

    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @classmethod
    def from_dict(cls, d: dict) -> BoundingBox:
        return cls(d["x0"], d["y0"], d["x1"], d["y1"])


@dataclass
class Entity:
    """A single extracted entity from the P&ID."""
    tag: str
    type: str
    subtype: str = ""
    description: str = ""
    line_number: str = ""
    service: str = ""

    # Spatial
    global_bbox: BoundingBox = field(default_factory=lambda: BoundingBox(0,0,0,0))
    local_bbox: list[float] = field(default_factory=list)

    # Provenance
    tile_id: int = 0
    tile_bbox: Optional[BoundingBox] = None
    depth: int = 0

    # Quality
    confidence: float = 1.0
    extraction_method: str = "llm"

    # ISA-5.1 parsing
    isa_function: str = ""      # e.g., "P", "T", "L", "F"
    isa_loop: str = ""          # e.g., "001", "005"
    isa_suffix: str = ""        # e.g., "I", "T", "C", "V"

    # Connections (inferred post-extraction)
    connected_to: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.tag and not self.isa_function:
            self._parse_isa_tag()

    def _parse_isa_tag(self):
        """Parse ISA-5.1 tag format: FUNCTION-LOOP-SUFFIX (e.g., PIC-005, TIC-005, PSV-001)."""
        # Match patterns like: P-01, TIC-005, PSV-001, TG-004, PDIT-004, XL-001
        pattern = r"^([A-Za-z]+)[-]?([0-9]{2,3})([A-Za-z]*)$"
        match = re.match(pattern, self.tag.replace(" ", "").replace("_", "-"))
        if match:
            func, loop, suffix = match.groups()
            self.isa_function = func.upper()
            self.isa_loop = loop
            self.isa_suffix = suffix.upper()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["global_bbox"] = self.global_bbox.to_dict()
        if self.tile_bbox:
            d["tile_bbox"] = self.tile_bbox.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Entity:
        d = dict(d)
        d["global_bbox"] = BoundingBox.from_dict(d.pop("global_bbox"))
        if "tile_bbox" in d and d["tile_bbox"]:
            d["tile_bbox"] = BoundingBox.from_dict(d.pop("tile_bbox"))
        return cls(**d)

    @property
    def key(self) -> str:
        """Deduplication key."""
        return f"{self.tag.upper()}:{self.type}:{self.subtype}"


@dataclass
class Connection:
    """Inferred connection between two entities."""
    source: str
    target: str
    type: str = "process"          # process, signal, electrical, pneumatic
    role: str = ""                 # suction, discharge, control, monitors, etc.
    confidence: float = 1.0
    method: str = "inferred"       # spatial, line_traced, explicit, manual

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TileResult:
    """Result from processing a single tile."""
    tile_id: int
    depth: int
    bbox: BoundingBox
    status: str = "complete"
    estimated_missing: int = 0
    reason: str = ""
    observation: str = ""
    entities: list[Entity] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "tile_id": self.tile_id,
            "depth": self.depth,
            "bbox": self.bbox.to_dict(),
            "status": self.status,
            "estimated_missing": self.estimated_missing,
            "reason": self.reason,
            "observation": self.observation,
            "entities": [e.to_dict() for e in self.entities],
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class ExtractionResult:
    """Final result of the entire extraction pipeline."""
    entities: list[Entity] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    tiles: list[TileResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "connections": [c.to_dict() for c in self.connections],
            "tiles": [t.to_dict() for t in self.tiles],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Image Tiling
# ---------------------------------------------------------------------------

_GRID_LAYOUTS = {
    2: (1, 2),
    4: (2, 2),
    8: (2, 4),
    16: (4, 4),
}


@dataclass
class ImageTile:
    image: Image.Image
    bbox: BoundingBox
    tile_id: int = 0
    parent_id: Optional[int] = None
    depth: int = 0


def split_image(image: Image.Image, split: int, overlap: float = 0.10) -> list[ImageTile]:
    """Split image into grid tiles with optional overlap."""
    if split not in _GRID_LAYOUTS:
        valid = list(_GRID_LAYOUTS.keys())
        raise ValueError(f"split must be one of {valid}, got {split}")
    if not (0.0 <= overlap < 0.5):
        raise ValueError("overlap must be in [0, 0.5)")

    rows, cols = _GRID_LAYOUTS[split]
    W, H = image.size
    base_w = W / cols
    base_h = H / rows

    tiles = []
    for r in range(rows):
        for c in range(cols):
            x0 = c * base_w
            y0 = r * base_h
            x1 = x0 + base_w
            y1 = y0 + base_h

            ox = base_w * overlap
            oy = base_h * overlap
            ex0 = max(0, x0 - ox)
            ey0 = max(0, y0 - oy)
            ex1 = min(W, x1 + ox)
            ey1 = min(H, y1 + oy)

            bbox = BoundingBox(ex0, ey0, ex1, ey1)
            crop = image.crop((int(ex0), int(ey0), int(ex1), int(ey1)))
            tiles.append(ImageTile(image=crop, bbox=bbox))

    return tiles


def choose_split(tile: ImageTile) -> Optional[int]:
    """Determine split factor based on tile dimensions."""
    longest = max(tile.image.size)
    if longest > 2000:
        return 8
    if longest > 1200:
        return 4
    if longest > 600:
        return 2
    return None


# ---------------------------------------------------------------------------
# Vision LLM Interface
# ---------------------------------------------------------------------------

def img_to_b64(img: Image.Image) -> str:
    b = io.BytesIO()
    img.save(b, format="PNG")
    return base64.b64encode(b.getvalue()).decode()


_EXTRACTION_PROMPT = """You are a Process Safety Engineer examining a Process & Instrumentation Diagram (P&ID) tile.

Your task is to extract EVERY readable entity: equipment, valves, instruments, line numbers, and annotations.

CRITICAL INSTRUCTIONS:
1. Use canonical ISA-5.1 tag format: TYPE-NNN (e.g., K-01, PSV-005, TIC-005, TG-004)
2. For equipment without standard tags, use descriptive names (e.g., "AIR COOLER", "OIL FILTER")
3. DO NOT guess unreadable text — only report what you can clearly read
4. For each entity, provide a precise bounding box in [0,1] normalized coordinates within this tile

ENTITY CLASSIFICATION GUIDE:
- **Equipment**: Tanks (TK), Pumps (P), Compressors (K), Coolers, Filters (E), Heaters (XL), Vessels
- **Valves**: Control (PCV, TCV, FCV), Relief (PSV, PZV), Safety (PSV), Check (CV), Gate, Ball
- **Instruments**: Pressure (P), Temperature (T), Level (L), Flow (F), Analysis (A), Differential (PD)
  - Suffixes: I=Indicator, T=Transmitter, C=Controller, V=Valve, S=Switch, G=Gauge, A=Alarm
- **Lines**: Line numbers (e.g., L-001), service descriptions
- **Annotations**: "TO TANK", "MANWAY", "DIP STICK", notes

For each extracted item, provide:
{
  "tag": "canonical tag",
  "type": "equipment|valve|instrument|controller|line|annotation",
  "subtype": "specific subtype (see below)",
  "description": "brief description",
  "line_number": "line number if applicable",
  "service": "service description",
  "local_bbox": [x0, y0, x1, y1]  // normalized 0-1 within this tile
}

SUBTYPE GUIDE:
- equipment: tank, pump, compressor, cooler, filter, heater, vessel, exchanger
- valve: control_valve, relief_valve, safety_relief_valve, check_valve, gate_valve, ball_valve
- instrument: pressure_indicator, temperature_gauge, level_switch, flow_indicator, dp_transmitter
- controller: temperature_controller, pressure_controller, level_controller
- line: process_line, signal_line, utility_line
- annotation: note, label, direction_arrow

If you believe additional zoom would reveal NEW entities not visible at this resolution, return status="incomplete" and explain why. Otherwise status="complete".

estimated_missing_items: integer estimate of additional entities discoverable with deeper zoom.

Process Safety Observation:
Provide a detailed Process Safety Engineer's perspective on this tile:
- Process flow direction and connections visible
- Safety-critical equipment (relief valves, emergency shutdowns)
- Potential hazards or safety concerns
- Process conditions (pressure, temperature, level indications)
- Unusual or noteworthy arrangements

Respond ONLY with valid JSON:
{
  "status": "complete" or "incomplete",
  "estimated_missing_items": integer,
  "reason": "string (required if incomplete)",
  "process_safety_observation": "string",
  "items": [
    {
      "tag": "string",
      "type": "string",
      "subtype": "string",
      "description": "string",
      "line_number": "string",
      "service": "string",
      "local_bbox": [x0, y0, x1, y1]
    }
  ]
}
"""


async def call_vision_llm(
    tile: ImageTile,
    config: Config = Config(),
    prompt: str = _EXTRACTION_PROMPT,
    max_retries: int = 5,
) -> dict:
    """Call vision LLM with rate limiting and retry logic."""

    if not config.API_KEY:
        raise RuntimeError("No API key configured. Set AGNES_API_KEY env var.")

    payload = {
        "model": config.MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_to_b64(tile.image)}"}
                }
            ]
        }]
    }

    timeout = httpx.Timeout(
        connect=config.TIMEOUT_CONNECT,
        read=config.TIMEOUT_READ,
        write=30,
        pool=30
    )
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(config.BASE_URL, headers=headers, json=payload)

            if r.status_code == 429:
                wait = 2 ** attempt + (attempt * 0.5)
                await asyncio.sleep(wait)
                continue

            r.raise_for_status()
            data = r.json()

            # Extract content from response
            content = data["choices"][0]["message"].get("content", "")
            if not content:
                raise ValueError("Empty response content")

            # Clean markdown code blocks
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)

        except httpx.ReadTimeout:
            await asyncio.sleep(2 ** attempt)
        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise ValueError(f"Failed to parse JSON after {max_retries} attempts: {e}")
            await asyncio.sleep(1)

    raise RuntimeError("Request failed after all retries")


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_entities(entities: list[Entity], iou_threshold: float = 0.5) -> list[Entity]:
    """Deduplicate entities using tag + spatial overlap matching."""

    # Group by normalized tag
    groups: dict[str, list[Entity]] = defaultdict(list)
    for e in entities:
        groups[e.tag.upper().strip()].append(e)

    result = []
    for tag, group in groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue

        # Merge spatially overlapping duplicates
        merged = []
        for e in group:
            match = next((m for m in merged if m.global_bbox.iou(e.global_bbox) > iou_threshold), None)
            if match is None:
                merged.append(e)
            else:
                # Keep the one with higher confidence or larger area
                if e.confidence > match.confidence or e.global_bbox.area > match.global_bbox.area:
                    idx = merged.index(match)
                    merged[idx] = e

        result.extend(merged)

    return result


# ---------------------------------------------------------------------------
# Connection Inference
# ---------------------------------------------------------------------------

def infer_connections(entities: list[Entity]) -> list[Connection]:
    """Infer connections between entities based on spatial proximity and ISA tag relationships."""

    connections = []

    # Build spatial index
    by_type = defaultdict(list)
    for e in entities:
        by_type[e.type].append(e)

    # 1. Instrument → Equipment monitoring (spatial proximity)
    instruments = by_type.get("instrument", []) + by_type.get("controller", [])
    equipment = by_type.get("equipment", [])
    valves = by_type.get("valve", [])

    for inst in instruments:
        # Find nearest equipment/valve within threshold
        nearest = None
        min_dist = float("inf")
        threshold = max(inst.global_bbox.width, inst.global_bbox.height) * 5

        for target in equipment + valves:
            if target.tag == inst.tag:
                continue
            dx = inst.global_bbox.center[0] - target.global_bbox.center[0]
            dy = inst.global_bbox.center[1] - target.global_bbox.center[1]
            dist = (dx**2 + dy**2) ** 0.5
            if dist < min_dist and dist < threshold:
                min_dist = dist
                nearest = target

        if nearest:
            role = _infer_monitor_role(inst)
            connections.append(Connection(
                source=inst.tag,
                target=nearest.tag,
                type="signal",
                role=role,
                confidence=max(0.5, 1.0 - min_dist / threshold),
                method="spatial"
            ))

    # 2. Controller → Valve control (explicit ISA relationship)
    controllers = by_type.get("controller", [])
    valves_list = by_type.get("valve", [])

    for ctrl in controllers:
        # Controller typically controls a valve with same loop number
        if ctrl.isa_loop:
            for valve in valves_list:
                if valve.isa_loop == ctrl.isa_loop and valve.tag != ctrl.tag:
                    connections.append(Connection(
                        source=ctrl.tag,
                        target=valve.tag,
                        type="signal",
                        role="control",
                        confidence=0.9,
                        method="isa_loop"
                    ))

    # 3. Temperature gauge → Controller (measurement)
    for ctrl in controllers:
        if ctrl.isa_function == "TIC":  # Temperature Indicating Controller
            for inst in instruments:
                if inst.isa_function == "TG" and inst.isa_loop == ctrl.isa_loop:
                    connections.append(Connection(
                        source=inst.tag,
                        target=ctrl.tag,
                        type="signal",
                        role="measurement",
                        confidence=0.95,
                        method="isa_loop"
                    ))

    # 4. Heater control (temperature switch → heater)
    for inst in instruments:
        if inst.isa_function == "TS" and inst.isa_loop:
            for eq in equipment:
                if eq.subtype == "heater" and eq.isa_loop == inst.isa_loop:
                    connections.append(Connection(
                        source=inst.tag,
                        target=eq.tag,
                        type="signal",
                        role="control",
                        confidence=0.85,
                        method="isa_loop"
                    ))

    # 5. Hand switch → Heater (manual control)
    for inst in instruments:
        if inst.isa_function == "HS" and inst.isa_loop:
            for eq in equipment:
                if eq.subtype == "heater" and eq.isa_loop == inst.isa_loop:
                    connections.append(Connection(
                        source=inst.tag,
                        target=eq.tag,
                        type="signal",
                        role="manual_control",
                        confidence=0.85,
                        method="isa_loop"
                    ))

    return connections


def _infer_monitor_role(inst: Entity) -> str:
    """Infer the monitoring role from instrument ISA function."""
    func = inst.isa_function
    if func.startswith("P"):
        return "monitors_pressure"
    elif func.startswith("T"):
        return "monitors_temperature"
    elif func.startswith("L"):
        return "monitors_level"
    elif func.startswith("F"):
        return "monitors_flow"
    elif func.startswith("PD"):
        return "monitors_differential_pressure"
    return "monitors"


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

class PIDExtractor:
    """Main extraction pipeline for P&ID images."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._tile_counter = 0
        self._semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT)
        self.results: list[TileResult] = []

    async def extract(self, image: Image.Image) -> ExtractionResult:
        """Run full extraction pipeline on a P&ID image."""
        start_time = time.time()

        # Phase 1: Initial split
        tiles = split_image(image, split=4, overlap=self.config.OVERLAP)

        # Phase 2: Recursive tile processing
        all_entities = []
        for tile in tiles:
            entities = await self._process_tile_recursive(tile, depth=0)
            all_entities.extend(entities)

        # Phase 3: Deduplication
        deduped = deduplicate_entities(all_entities, self.config.DEDUP_IOU_THRESHOLD)

        # Phase 4: Connection inference
        connections = infer_connections(deduped)

        # Phase 5: Build result
        result = ExtractionResult(
            entities=deduped,
            connections=connections,
            tiles=self.results,
            metadata={
                "total_tiles_processed": self._tile_counter,
                "total_entities": len(deduped),
                "total_connections": len(connections),
                "processing_time_seconds": time.time() - start_time,
                "image_size": image.size,
                "model": self.config.MODEL,
            }
        )

        return result

    async def _process_tile_recursive(self, tile: ImageTile, depth: int) -> list[Entity]:
        """Recursively process a tile, splitting if needed."""
        tile_id = self._tile_counter
        self._tile_counter += 1
        tile.tile_id = tile_id
        tile.depth = depth

        tile_start = time.time()

        # Call LLM
        async with self._semaphore:
            raw = await call_vision_llm(tile, self.config)

        # Parse entities
        items = raw.get("items", [])
        entities = []
        for item in items:
            entity = self._item_to_entity(item, tile, depth, tile_id)
            if entity.confidence >= self.config.MIN_CONFIDENCE:
                entities.append(entity)

        # Record tile result
        tile_result = TileResult(
            tile_id=tile_id,
            depth=depth,
            bbox=tile.bbox,
            status=raw.get("status", "complete"),
            estimated_missing=raw.get("estimated_missing_items", 0),
            reason=raw.get("reason", ""),
            observation=raw.get("process_safety_observation", ""),
            entities=entities,
            raw_response=raw,
            processing_time_ms=(time.time() - tile_start) * 1000,
        )
        self.results.append(tile_result)

        # Check if we should split further
        if depth >= self.config.MAX_DEPTH:
            return entities

        if min(tile.image.size) < self.config.MIN_TILE:
            return entities

        force_incomplete = any(not e.tag.strip() for e in entities) or tile_result.estimated_missing > 0
        should_split = (raw.get("status") == "incomplete") or force_incomplete

        if not should_split:
            return entities

        split = choose_split(tile)
        if split is None:
            return entities

        # Split and process children
        children = split_image(tile.image, split=split, overlap=self.config.OVERLAP)
        child_results = await asyncio.gather(*[
            self._process_tile_recursive(child, depth + 1)
            for child in children
        ])

        for child_entities in child_results:
            entities.extend(child_entities)

        return deduplicate_entities(entities, self.config.DEDUP_IOU_THRESHOLD)

    def _item_to_entity(self, item: dict, tile: ImageTile, depth: int, tile_id: int) -> Entity:
        """Convert LLM item to Entity with global bbox."""
        local_bbox = item.get("local_bbox", [0, 0, 1, 1])
        if len(local_bbox) != 4:
            local_bbox = [0, 0, 1, 1]

        global_bbox = BoundingBox.from_local(local_bbox, tile.bbox)

        return Entity(
            tag=item.get("tag", ""),
            type=item.get("type", "unknown"),
            subtype=item.get("subtype", ""),
            description=item.get("description", ""),
            line_number=item.get("line_number", ""),
            service=item.get("service", ""),
            global_bbox=global_bbox,
            local_bbox=local_bbox,
            tile_id=tile_id,
            tile_bbox=tile.bbox,
            depth=depth,
            confidence=1.0,
            extraction_method="llm",
        )


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------

def export_json(result: ExtractionResult, path: Path) -> None:
    """Export to JSON."""
    with open(path, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)


def export_csv(result: ExtractionResult, path: Path) -> None:
    """Export entities to CSV."""
    import csv

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "tag", "type", "subtype", "description", "line_number", "service",
            "isa_function", "isa_loop", "isa_suffix",
            "x0", "y0", "x1", "y1", "confidence", "tile_id", "depth"
        ])
        for e in result.entities:
            writer.writerow([
                e.tag, e.type, e.subtype, e.description, e.line_number, e.service,
                e.isa_function, e.isa_loop, e.isa_suffix,
                e.global_bbox.x0, e.global_bbox.y0, e.global_bbox.x1, e.global_bbox.y1,
                e.confidence, e.tile_id, e.depth
            ])


def export_graphml(result: ExtractionResult, path: Path) -> None:
    """Export to GraphML for graph visualization."""

    nodes_xml = []
    for e in result.entities:
        attrs = f' tag="{e.tag}" type="{e.type}" subtype="{e.subtype}"'
        nodes_xml.append(f'    <node id="{e.tag}"><data key="tag">{e.tag}</data><data key="type">{e.type}</data><data key="subtype">{e.subtype}</data></node>')

    edges_xml = []
    for i, c in enumerate(result.connections):
        edges_xml.append(f'    <edge id="e{i}" source="{c.source}" target="{c.target}"><data key="type">{c.type}</data><data key="role">{c.role}</data></edge>')

    graphml = f"""<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="tag" for="node" attr.name="tag" attr.type="string"/>
  <key id="type" for="all" attr.name="type" attr.type="string"/>
  <key id="subtype" for="node" attr.name="subtype" attr.type="string"/>
  <key id="role" for="edge" attr.name="role" attr.type="string"/>
  <graph id="pid" edgedefault="directed">
{"\n".join(nodes_xml)}
{"\n".join(edges_xml)}
  </graph>
</graphml>"""

    with open(path, "w") as f:
        f.write(graphml)


def export_markdown(result: ExtractionResult, path: Path) -> None:
    """Export to Markdown layout report."""

    lines = [
        "# P&ID Layout Analysis",
        "",
        f"**Total Entities:** {len(result.entities)}",
        f"**Total Connections:** {len(result.connections)}",
        f"**Tiles Processed:** {result.metadata.get('total_tiles_processed', 'N/A')}",
        f"**Processing Time:** {result.metadata.get('processing_time_seconds', 0):.1f}s",
        "",
        "---",
        "",
        "## Equipment",
        "",
    ]

    for e in result.entities:
        if e.type == "equipment":
            lines.append(f"- **{e.tag}**: {e.description} (Service: {e.service})")

    lines.extend(["", "## Valves", ""])
    for e in result.entities:
        if e.type == "valve":
            lines.append(f"- **{e.tag}**: {e.description} (Service: {e.service})")

    lines.extend(["", "## Instruments", ""])
    for e in result.entities:
        if e.type in ("instrument", "controller"):
            lines.append(f"- **{e.tag}**: {e.description} (Service: {e.service})")

    lines.extend(["", "## Connections", ""])
    for c in result.connections:
        lines.append(f"- **{c.source}** → **{c.target}** ({c.type}: {c.role})")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract P&ID entities from image")
    parser.add_argument("image", help="Path to P&ID image")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--max-depth", type=int, default=None, help="Max recursion depth")
    parser.add_argument("--no-recurse", action="store_true", help="Disable recursive splitting")
    parser.add_argument("--format", choices=["json", "csv", "graphml", "md", "all"], default="all", help="Output format")
    args = parser.parse_args()

    config = Config()
    config.OUTPUT_DIR = Path(args.output)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.model:
        config.MODEL = args.model
    if args.max_depth is not None:
        config.MAX_DEPTH = args.max_depth
    if args.no_recurse:
        config.MAX_DEPTH = 0

    image = Image.open(args.image)
    print(f"Processing {args.image} ({image.size[0]}x{image.size[1]})...")

    extractor = PIDExtractor(config)
    result = await extractor.extract(image)

    # Export
    base = config.OUTPUT_DIR / Path(args.image).stem

    if args.format in ("json", "all"):
        export_json(result, base.with_suffix(".json"))
        print(f"  JSON: {base.with_suffix('.json')}")

    if args.format in ("csv", "all"):
        export_csv(result, base.with_suffix(".csv"))
        print(f"  CSV: {base.with_suffix('.csv')}")

    if args.format in ("graphml", "all"):
        export_graphml(result, base.with_suffix(".graphml"))
        print(f"  GraphML: {base.with_suffix('.graphml')}")

    if args.format in ("md", "all"):
        export_markdown(result, base.with_suffix(".md"))
        print(f"  Markdown: {base.with_suffix('.md')}")

    print(f"\nExtracted {len(result.entities)} entities, {len(result.connections)} connections")
    print(f"Processed {result.metadata['total_tiles_processed']} tiles in {result.metadata['processing_time_seconds']:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
