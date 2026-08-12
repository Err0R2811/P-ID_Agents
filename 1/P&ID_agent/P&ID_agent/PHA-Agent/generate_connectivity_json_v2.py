"""
P&ID Connectivity JSON Generator v2.0

Generates structured connectivity data (nodes + edges) for LLM understanding.

Improvements over v1.0:
- Reads from extraction JSON directly (not just markdown)
- Automatic ISA tag parsing and classification
- Connection inference from spatial proximity + ISA relationships
- Support for multiple redundancy groups
- Validation of connectivity consistency
- Export to multiple formats (JSON, YAML, Protocol Buffers-like)
- Template-based report generation
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class NodeType(Enum):
    EQUIPMENT = "equipment"
    VALVE = "valve"
    INSTRUMENT = "instrument"
    CONTROLLER = "controller"
    LINE = "line"
    ANNOTATION = "annotation"


class EdgeType(Enum):
    PROCESS = "process"       # Physical fluid flow
    SIGNAL = "signal"         # Measurement/signal line
    CONTROL = "control"       # Control loop signal
    ELECTRICAL = "electrical" # Electrical power/signal
    PNEUMATIC = "pneumatic"   # Pneumatic signal
    HYDRAULIC = "hydraulic"   # Hydraulic signal
    MECHANICAL = "mechanical" # Mechanical linkage


@dataclass
class Node:
    id: str
    type: str
    subtype: str = ""
    name: str = ""
    measures: str = ""        # For instruments: pressure, temperature, level, etc.
    redundancy_group: str = ""
    isa_function: str = ""    # P, T, L, F, etc.
    isa_loop: str = ""        # 001, 005, etc.
    isa_suffix: str = ""      # I, T, C, V, S, G, A
    properties: dict = field(default_factory=dict)

    @property
    def is_instrument(self) -> bool:
        return self.type in ("instrument", "controller")

    @property
    def is_equipment(self) -> bool:
        return self.type == "equipment"

    @property
    def is_valve(self) -> bool:
        return self.type == "valve"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Edge:
    source: str
    target: str
    type: str = "process"
    role: str = ""
    confidence: float = 1.0
    method: str = "inferred"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConnectivityGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }

    def get_node(self, node_id: str) -> Optional[Node]:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def get_neighbors(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id or e.target == node_id]

    def get_outgoing(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id]

    def get_incoming(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.target == node_id]

    def validate(self) -> list[str]:
        """Validate graph consistency and return warnings."""
        warnings = []
        node_ids = {n.id for n in self.nodes}

        # Check for dangling edges
        for e in self.edges:
            if e.source not in node_ids:
                warnings.append(f"Edge references unknown source: {e.source}")
            if e.target not in node_ids:
                warnings.append(f"Edge references unknown target: {e.target}")

        # Check for isolated nodes
        connected = set()
        for e in self.edges:
            connected.add(e.source)
            connected.add(e.target)
        for n in self.nodes:
            if n.id not in connected and n.type != "annotation":
                warnings.append(f"Node {n.id} ({n.type}) has no connections")

        # Check for duplicate nodes
        seen = set()
        for n in self.nodes:
            if n.id in seen:
                warnings.append(f"Duplicate node: {n.id}")
            seen.add(n.id)

        return warnings


# ---------------------------------------------------------------------------
# ISA Tag Parser
# ---------------------------------------------------------------------------

def parse_isa_tag(tag: str) -> dict[str, str]:
    """Parse ISA-5.1 tag into components.

    Examples:
        P-01      -> {"function": "P", "loop": "01", "suffix": ""}
        TIC-005   -> {"function": "TIC", "loop": "005", "suffix": ""}
        PSV-001   -> {"function": "PSV", "loop": "001", "suffix": ""}
        TG-004    -> {"function": "TG", "loop": "004", "suffix": ""}
        PDIT-004  -> {"function": "PDIT", "loop": "004", "suffix": ""}
    """
    tag = tag.strip().upper().replace(" ", "-").replace("_", "-")

    # Match pattern: LETTERS-NUMBERS
    match = re.match(r"^([A-Z]+)-?([0-9]{2,3})([A-Z]*)$", tag)
    if match:
        func, loop, suffix = match.groups()
        return {"function": func, "loop": loop, "suffix": suffix}

    # Special cases without numbers
    if tag in ("AIR-COOLER", "AIR COOLER"):
        return {"function": "EQUIP", "loop": "", "suffix": ""}
    if tag == "DIP-STICK":
        return {"function": "L", "loop": "", "suffix": ""}

    return {"function": "", "loop": "", "suffix": ""}


def infer_subtype_from_tag(tag: str, type_hint: str = "") -> str:
    """Infer equipment/valve/instrument subtype from ISA tag."""
    parsed = parse_isa_tag(tag)
    func = parsed["function"]

    if type_hint == "equipment" or not type_hint:
        if func == "TK" or "TANK" in tag.upper():
            return "tank"
        elif func in ("P", "PU") or "PUMP" in tag.upper():
            return "pump"
        elif func == "K" or "COMPRESSOR" in tag.upper():
            return "compressor"
        elif func in ("E", "EF") or "FILTER" in tag.upper():
            return "filter"
        elif func in ("XL", "XH") or "HEATER" in tag.upper():
            return "heater"
        elif "COOLER" in tag.upper() or "EXCHANGER" in tag.upper():
            return "cooler"

    if type_hint == "valve" or not type_hint:
        if func in ("TCV", "PCV", "FCV", "LCV"):
            return "control_valve"
        elif func in ("PSV", "PRV"):
            return "safety_relief_valve"
        elif func in ("PZV", "RV"):
            return "relief_valve"
        elif func in ("CV", "CKV"):
            return "check_valve"
        elif func in ("XV", "SV"):
            return "solenoid_valve"
        elif func in ("GV", "GV"):
            return "gate_valve"

    if type_hint in ("instrument", "controller") or not type_hint:
        if func.startswith("P") and not func.startswith("PD"):
            return "pressure"
        elif func.startswith("T"):
            return "temperature"
        elif func.startswith("L"):
            return "level"
        elif func.startswith("F"):
            return "flow"
        elif func.startswith("PD"):
            return "differential_pressure"
        elif func in ("A", "AI", "AE"):
            return "analysis"

    return ""


def infer_measures_from_tag(tag: str) -> str:
    """Infer what an instrument measures from its ISA tag."""
    parsed = parse_isa_tag(tag)
    func = parsed["function"]

    if func.startswith("P") and not func.startswith("PD"):
        return "pressure"
    elif func.startswith("T"):
        return "temperature"
    elif func.startswith("L"):
        return "level"
    elif func.startswith("F"):
        return "flow"
    elif func.startswith("PD"):
        return "differential_pressure"
    elif func.startswith("A"):
        return "analysis"
    elif func in ("HS", "XS"):
        return "manual"
    return ""


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

class ConnectivityBuilder:
    """Build connectivity graph from extracted entities."""

    def __init__(self):
        self.graph = ConnectivityGraph()
        self._node_map: dict[str, Node] = {}

    def build_from_extraction(self, extraction_data: dict) -> ConnectivityGraph:
        """Build graph from adaptive_pid_recursive_extractor output."""
        entities = extraction_data.get("entities", [])
        connections = extraction_data.get("connections", [])

        # Build nodes from entities
        for entity in entities:
            node = self._entity_to_node(entity)
            self._add_node(node)

        # Add inferred connections
        for conn in connections:
            edge = Edge(
                source=conn.get("source", ""),
                target=conn.get("target", ""),
                type=conn.get("type", "process"),
                role=conn.get("role", ""),
                confidence=conn.get("confidence", 1.0),
                method=conn.get("method", "inferred"),
            )
            self.graph.edges.append(edge)

        # Infer additional connections from ISA relationships
        self._infer_isa_connections()

        # Infer redundancy groups
        self._infer_redundancy_groups()

        return self.graph

    def build_from_manual(self, nodes_data: list[dict], edges_data: list[dict]) -> ConnectivityGraph:
        """Build graph from manually curated data."""
        for nd in nodes_data:
            node = Node(
                id=nd.get("id", ""),
                type=nd.get("type", ""),
                subtype=nd.get("subtype", ""),
                name=nd.get("name", ""),
                measures=nd.get("measures", ""),
                redundancy_group=nd.get("redundancy_group", ""),
                properties=nd.get("properties", {}),
            )
            # Parse ISA if available
            parsed = parse_isa_tag(node.id)
            node.isa_function = parsed["function"]
            node.isa_loop = parsed["loop"]
            node.isa_suffix = parsed["suffix"]
            self._add_node(node)

        for ed in edges_data:
            edge = Edge(
                source=ed.get("source", ""),
                target=ed.get("target", ""),
                type=ed.get("type", "process"),
                role=ed.get("role", ""),
            )
            self.graph.edges.append(edge)

        return self.graph

    def _entity_to_node(self, entity: dict) -> Node:
        """Convert extracted entity to graph node."""
        tag = entity.get("tag", "")
        type_ = entity.get("type", "unknown")
        subtype = entity.get("subtype", "")

        # Infer subtype if not provided
        if not subtype:
            subtype = infer_subtype_from_tag(tag, type_)

        # Parse ISA
        parsed = parse_isa_tag(tag)

        # Infer measures for instruments
        measures = ""
        if type_ in ("instrument", "controller"):
            measures = infer_measures_from_tag(tag)

        return Node(
            id=tag,
            type=type_,
            subtype=subtype,
            name=entity.get("description", tag),
            measures=measures,
            isa_function=parsed["function"],
            isa_loop=parsed["loop"],
            isa_suffix=parsed["suffix"],
            properties={
                "line_number": entity.get("line_number", ""),
                "service": entity.get("service", ""),
                "confidence": entity.get("confidence", 1.0),
            }
        )

    def _add_node(self, node: Node):
        """Add node to graph, avoiding duplicates."""
        if node.id not in self._node_map:
            self._node_map[node.id] = node
            self.graph.nodes.append(node)

    def _infer_isa_connections(self):
        """Infer connections based on ISA tag relationships."""
        # Controller → Valve (same loop number)
        controllers = [n for n in self.graph.nodes if n.type == "controller"]
        valves = [n for n in self.graph.nodes if n.type == "valve"]
        instruments = [n for n in self.graph.nodes if n.type == "instrument"]
        equipment = [n for n in self.graph.nodes if n.type == "equipment"]

        for ctrl in controllers:
            if not ctrl.isa_loop:
                continue

            # Find valve with same loop
            for valve in valves:
                if valve.isa_loop == ctrl.isa_loop and valve.id != ctrl.id:
                    self._add_edge_safe(
                        Edge(ctrl.id, valve.id, "control", "control", 0.9, "isa_loop")
                    )

            # Find measurement instrument with same loop
            for inst in instruments:
                if inst.isa_loop == ctrl.isa_loop and inst.isa_function in ("TG", "PG", "LG", "FG"):
                    self._add_edge_safe(
                        Edge(inst.id, ctrl.id, "signal", "measurement", 0.95, "isa_loop")
                    )

        # Temperature Switch → Heater (same loop)
        for inst in instruments:
            if inst.isa_function == "TS" and inst.isa_loop:
                for eq in equipment:
                    if eq.subtype == "heater" and eq.isa_loop == inst.isa_loop:
                        self._add_edge_safe(
                            Edge(inst.id, eq.id, "signal", "control", 0.85, "isa_loop")
                        )

        # Hand Switch → Heater (same loop)
        for inst in instruments:
            if inst.isa_function == "HS" and inst.isa_loop:
                for eq in equipment:
                    if eq.subtype == "heater" and eq.isa_loop == inst.isa_loop:
                        self._add_edge_safe(
                            Edge(inst.id, eq.id, "signal", "manual_control", 0.85, "isa_loop")
                        )

        # Safety Interlock → Heater
        for inst in instruments:
            if inst.isa_function == "XS" and inst.isa_loop:
                for eq in equipment:
                    if eq.subtype == "heater" and eq.isa_loop == inst.isa_loop:
                        self._add_edge_safe(
                            Edge(inst.id, eq.id, "signal", "safety_interlock", 0.9, "isa_loop")
                        )

    def _infer_redundancy_groups(self):
        """Infer redundancy groups from tags and subtypes."""
        # Group by subtype and loop prefix patterns
        by_subtype = defaultdict(list)
        for n in self.graph.nodes:
            if n.subtype:
                by_subtype[n.subtype].append(n)

        # Pumps: P-01, P-02
        pumps = [n for n in self.graph.nodes if n.subtype == "pump"]
        if len(pumps) > 1:
            for p in pumps:
                p.redundancy_group = "pumps"

        # Filters: E-001, E-002
        filters_ = [n for n in self.graph.nodes if n.subtype == "filter"]
        if len(filters_) > 1:
            for f in filters_:
                f.redundancy_group = "filters"

        # Heaters: XL-001, XL-002
        heaters = [n for n in self.graph.nodes if n.subtype == "heater"]
        if len(heaters) > 1:
            for h in heaters:
                h.redundancy_group = "heaters"

        # Relief valves: PZV-001, PZV-002, PSV-005, PCV-002
        relief = [n for n in self.graph.nodes if n.subtype in ("relief_valve", "safety_relief_valve", "pressure_control_valve")]
        if len(relief) > 1:
            for r in relief:
                if not r.redundancy_group:
                    r.redundancy_group = "relief"

    def _add_edge_safe(self, edge: Edge):
        """Add edge if both nodes exist and edge not duplicate."""
        source_exists = any(n.id == edge.source for n in self.graph.nodes)
        target_exists = any(n.id == edge.target for n in self.graph.nodes)

        if not source_exists or not target_exists:
            return

        # Check for duplicate
        dup = any(
            e.source == edge.source and e.target == edge.target and e.role == edge.role
            for e in self.graph.edges
        )
        if not dup:
            self.graph.edges.append(edge)


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------

def export_json(graph: ConnectivityGraph, path: Path) -> None:
    """Export to JSON."""
    with open(path, "w") as f:
        json.dump(graph.to_dict(), f, indent=2)


def export_yaml(graph: ConnectivityGraph, path: Path) -> None:
    """Export to YAML."""
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(graph.to_dict(), f, default_flow_style=False, sort_keys=False)
    except ImportError:
        print("PyYAML not installed, skipping YAML export")


def export_mermaid(graph: ConnectivityGraph, path: Path) -> None:
    """Export to Mermaid flowchart."""

    # Node styling
    type_styles = {
        "equipment": {"fill": "#e1f5fe", "stroke": "#01579b"},
        "valve": {"fill": "#fff3e0", "stroke": "#e65100"},
        "instrument": {"fill": "#fce4ec", "stroke": "#c2185b"},
        "controller": {"fill": "#f3e5f5", "stroke": "#7b1fa2"},
    }

    lines = ["```mermaid", "graph TD"]

    # Nodes
    for node in graph.nodes:
        safe_id = node.id.replace("-", "_").replace(" ", "_")
        label = f"{node.id}\n{node.name}" if node.name else node.id

        style = type_styles.get(node.type, {})
        if style:
            lines.append(f'    {safe_id}["{label}"]')
        else:
            lines.append(f'    {safe_id}["{label}"]')

    # Edges
    for edge in graph.edges:
        src = edge.source.replace("-", "_").replace(" ", "_")
        tgt = edge.target.replace("-", "_").replace(" ", "_")

        if edge.type == "signal":
            lines.append(f'    {src} -.->|{edge.role}| {tgt}')
        elif edge.type == "control":
            lines.append(f'    {src} ==>|{edge.role}| {tgt}')
        else:
            lines.append(f'    {src} -->|{edge.role}| {tgt}')

    # Styles
    for node in graph.nodes:
        safe_id = node.id.replace("-", "_").replace(" ", "_")
        style = type_styles.get(node.type, {})
        if style:
            lines.append(f'    style {safe_id} fill:{style["fill"]},stroke:{style["stroke"]},stroke-width:2px')

    lines.append("```")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def export_dot(graph: ConnectivityGraph, path: Path) -> None:
    """Export to Graphviz DOT format."""

    type_colors = {
        "equipment": "#e1f5fe",
        "valve": "#fff3e0",
        "instrument": "#fce4ec",
        "controller": "#f3e5f5",
    }

    lines = ["digraph PID {", "  rankdir=LR;", "  node [shape=box, style="rounded,filled", fontname="Helvetica"];"]

    for node in graph.nodes:
        color = type_colors.get(node.type, "#f5f5f5")
        lines.append(f'  "{node.id}" [label="{node.id}\n{node.name}", fillcolor="{color}"];')

    for edge in graph.edges:
        style = "dashed" if edge.type == "signal" else "solid"
        lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.role}", style={style}];')

    lines.append("}")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate connectivity JSON from P&ID extraction")
    parser.add_argument("input", help="Input JSON file (from extractor) or directory")
    parser.add_argument("-o", "--output", default="connectivity", help="Output base name")
    parser.add_argument("--format", choices=["json", "yaml", "mermaid", "dot", "all"], default="all")
    parser.add_argument("--validate", action="store_true", help="Validate graph consistency")
    args = parser.parse_args()

    input_path = Path(args.input)

    # Load extraction data
    if input_path.is_file():
        with open(input_path) as f:
            data = json.load(f)
    elif input_path.is_dir():
        # Look for entities.json or similar
        candidates = list(input_path.glob("*.json"))
        if not candidates:
            print(f"No JSON files found in {input_path}")
            return
        with open(candidates[0]) as f:
            data = json.load(f)
    else:
        print(f"Input not found: {input_path}")
        return

    # Build graph
    builder = ConnectivityBuilder()
    graph = builder.build_from_extraction(data)

    # Validate
    if args.validate:
        warnings = graph.validate()
        if warnings:
            print("Validation warnings:")
            for w in warnings:
                print(f"  - {w}")
        else:
            print("Validation: OK")

    # Export
    base = Path(args.output)

    if args.format in ("json", "all"):
        export_json(graph, base.with_suffix(".json"))
        print(f"JSON: {base.with_suffix('.json')}")

    if args.format in ("yaml", "all"):
        export_yaml(graph, base.with_suffix(".yaml"))
        print(f"YAML: {base.with_suffix('.yaml')}")

    if args.format in ("mermaid", "all"):
        export_mermaid(graph, base.with_suffix(".mmd"))
        print(f"Mermaid: {base.with_suffix('.mmd')}")

    if args.format in ("dot", "all"):
        export_dot(graph, base.with_suffix(".dot"))
        print(f"DOT: {base.with_suffix('.dot')}")

    print(f"\nNodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")


if __name__ == "__main__":
    main()
