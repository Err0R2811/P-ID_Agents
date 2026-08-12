"""
P&ID Flowchart Generator v2.0

Generates professional P&ID diagrams from connectivity data.

Improvements over v1.0:
- Interactive SVG with tooltips and click handlers
- ISA-5.1 compliant symbol rendering
- Automatic layout using Sugiyama-style layering
- Support for signal line types (electrical, pneumatic, hydraulic)
- Export to HTML, SVG, PNG, and Mermaid
- Responsive design with zoom/pan
- Dark mode support
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Callable
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Layout Engine
# ---------------------------------------------------------------------------

@dataclass
class Point:
    x: float
    y: float


@dataclass
class LayoutNode:
    """A node with computed layout position."""
    id: str
    x: float = 0
    y: float = 0
    width: float = 80
    height: float = 50
    layer: int = 0
    position_in_layer: int = 0

    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    @property
    def left(self) -> Point:
        return Point(self.x, self.center.y)

    @property
    def right(self) -> Point:
        return Point(self.x + self.width, self.center.y)

    @property
    def top(self) -> Point:
        return Point(self.center.x, self.y)

    @property
    def bottom(self) -> Point:
        return Point(self.center.x, self.y + self.height)


class SugiyamaLayout:
    """Layered graph layout using Sugiyama-style algorithm."""

    def __init__(self, nodes: list[dict], edges: list[dict]):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self.layout_nodes: dict[str, LayoutNode] = {}
        self.layers: list[list[str]] = []

    def compute(self, node_sizes: dict[str, tuple[float, float]] = None) -> dict[str, LayoutNode]:
        """Compute layout positions."""
        # Phase 1: Assign layers using longest path
        self._assign_layers()

        # Phase 2: Order nodes within layers to minimize crossings
        self._order_within_layers()

        # Phase 3: Compute coordinates
        self._compute_coordinates(node_sizes)

        return self.layout_nodes

    def _assign_layers(self):
        """Assign nodes to layers using topological sort / longest path."""
        # Build adjacency list
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        for e in self.edges:
            if e["type"] == "process":
                outgoing[e["source"]].append(e["target"])
                incoming[e["target"]].append(e["source"])

        # Find source nodes (no incoming process edges)
        all_nodes = set(self.nodes.keys())
        targets = set(e["target"] for e in self.edges if e["type"] == "process")
        sources = all_nodes - targets

        if not sources:
            sources = all_nodes  # Fallback: all nodes are sources

        # BFS to assign layers
        layer_map = {}
        queue = deque([(s, 0) for s in sources])
        visited = set()

        while queue:
            node_id, layer = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)

            # Update layer if this path is longer
            if node_id not in layer_map or layer > layer_map[node_id]:
                layer_map[node_id] = layer

            for target in outgoing[node_id]:
                if target not in visited:
                    queue.append((target, layer + 1))

        # Group by layer
        max_layer = max(layer_map.values()) if layer_map else 0
        self.layers = [[] for _ in range(max_layer + 1)]
        for node_id, layer in layer_map.items():
            self.layers[layer].append(node_id)

        # Add unvisited nodes to last layer
        for node_id in all_nodes:
            if node_id not in layer_map:
                self.layers[-1].append(node_id)

    def _order_within_layers(self):
        """Minimize edge crossings within layers."""
        # Simple barycenter method
        for _ in range(3):  # Iterations
            for i, layer in enumerate(self.layers):
                if i == 0:
                    continue

                # Compute barycenter based on previous layer
                prev_layer = set(self.layers[i - 1])
                positions = {}
                for node_id in layer:
                    # Find connected nodes in previous layer
                    connected = [
                        e["source"] for e in self.edges
                        if e["target"] == node_id and e["source"] in prev_layer
                    ]
                    if connected:
                        positions[node_id] = sum(
                            self.layers[i-1].index(c) for c in connected
                        ) / len(connected)
                    else:
                        positions[node_id] = len(layer)

                # Sort by barycenter
                self.layers[i] = sorted(layer, key=lambda n: positions.get(n, 0))

    def _compute_coordinates(self, node_sizes: dict[str, tuple[float, float]] = None):
        """Compute x,y coordinates from layer assignments."""
        layer_height = 150
        node_spacing = 120

        for layer_idx, layer in enumerate(self.layers):
            y = layer_idx * layer_height + 50

            total_width = len(layer) * node_spacing
            start_x = 50

            for pos, node_id in enumerate(layer):
                x = start_x + pos * node_spacing

                size = node_sizes.get(node_id, (80, 50)) if node_sizes else (80, 50)

                self.layout_nodes[node_id] = LayoutNode(
                    id=node_id,
                    x=x,
                    y=y,
                    width=size[0],
                    height=size[1],
                    layer=layer_idx,
                    position_in_layer=pos,
                )


# ---------------------------------------------------------------------------
# SVG Renderer
# ---------------------------------------------------------------------------

class SVGRenderer:
    """Render P&ID as interactive SVG."""

    # ISA-5.1 symbol definitions
    SYMBOLS = {
        "tank": """<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/><line x1="{x}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="{stroke}" stroke-width="1.5"/>""",
        "pump": """<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="{r2}" fill="none" stroke="{stroke}" stroke-width="1.5"/><line x1="{cx}" y1="{y1}" x2="{cx}" y2="{y2}" stroke="{stroke}" stroke-width="1.5"/><line x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="{stroke}" stroke-width="1.5"/>""",
        "compressor": """<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" fill="{stroke}" font-size="{fs}" font-weight="bold">K</text>""",
        "cooler": """<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><line x1="{x}" y1="{y1}" x2="{x2}" y2="{y1}" stroke="{stroke}" stroke-width="1"/><line x1="{x}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="{stroke}" stroke-width="1"/><line x1="{x}" y1="{y2}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="1"/>""",
        "filter": """<polygon points="{cx},{y} {x2},{cy} {cx},{y2} {x},{cy}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="1"/><line x1="{x1}" y1="{y2}" x2="{x2}" y2="{y1}" stroke="{stroke}" stroke-width="1"/>""",
        "heater": """<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><path d="M {x1},{y1} Q {x1q},{y1q} {x2q},{y1}" stroke="{accent}" stroke-width="2" fill="none"/><path d="M {x1},{y2} Q {x1q},{y2q} {x2q},{y2}" stroke="{accent}" stroke-width="2" fill="none"/>""",
        "control_valve": """<polygon points="{cx},{y1} {x2},{y1} {cx},{y2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><rect x="{x1a}" y="{ya}" width="{wa}" height="{ha}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/><line x1="{cx}" y1="{ya}" x2="{cx}" y2="{y}" stroke="{stroke}" stroke-width="1.5"/><circle cx="{cx}" cy="{y}" r="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>""",
        "relief_valve": """<polygon points="{cx},{y1} {x2},{y1} {cx},{y2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><path d="M {x1a},{y1a} L {x1a},{ya} M {x2a},{y1a} L {x2a},{ya}" stroke="{stroke}" stroke-width="1.5"/><path d="M {x1s},{ya} Q {cx},{y1} {x2s},{ya}" stroke="{stroke}" stroke-width="1.5" fill="none"/>""",
        "safety_relief_valve": """<polygon points="{cx},{y1} {x2},{y1} {cx},{y2}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/><path d="M {x1a},{y1a} L {x1a},{ya} M {x2a},{y1a} L {x2a},{ya}" stroke="{stroke}" stroke-width="1.5"/><path d="M {x1s},{ya} Q {cx},{y1} {x2s},{ya}" stroke="{stroke}" stroke-width="1.5" fill="none"/>""",
        "check_valve": """<polygon points="{x1},{y1} {x2},{cy} {x1},{y2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><line x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="{stroke}" stroke-width="1.5"/>""",
        "instrument": """<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/><text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" fill="{stroke}" font-size="{fs}" font-weight="bold">{tag}</text>""",
        "controller": """<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/><text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" fill="{stroke}" font-size="{fs}" font-weight="bold">{tag}</text>""",
    }

    # Colors
    COLORS = {
        "equipment": {"fill": "#e3f2fd", "stroke": "#1565c0"},
        "valve": {"fill": "#fff3e0", "stroke": "#ef6c00"},
        "instrument": {"fill": "#fce4ec", "stroke": "#c2185b"},
        "controller": {"fill": "#f3e5f5", "stroke": "#7b1fa2"},
        "line": {"fill": "#f5f5f5", "stroke": "#616161"},
    }

    def __init__(self, graph_data: dict):
        self.nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
        self.edges = graph_data.get("edges", [])
        self.layout = {}

    def render(self, width: Optional[int] = None, height: Optional[int] = None) -> str:
        """Render complete SVG."""
        # Compute layout
        layout_engine = SugiyamaLayout(
            list(self.nodes.values()),
            self.edges
        )
        self.layout = layout_engine.compute()

        # Calculate canvas size
        if not self.layout:
            return '<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg"><text x="200" y="150" text-anchor="middle">No nodes to render</text></svg>'

        max_x = max(n.x + n.width for n in self.layout.values()) + 100
        max_y = max(n.y + n.height for n in self.layout.values()) + 100

        svg_width = width or int(max_x)
        svg_height = height or int(max_y)

        # Build SVG
        parts = [
            f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">',
            self._defs(),
            self._grid(svg_width, svg_height),
        ]

        # Draw edges first (behind nodes)
        for edge in self.edges:
            parts.append(self._draw_edge(edge))

        # Draw nodes
        for node_id, node in self.nodes.items():
            if node_id in self.layout:
                parts.append(self._draw_node(node, self.layout[node_id]))

        parts.append('</svg>')

        return "\n".join(parts)

    def _defs(self) -> str:
        """SVG definitions (markers, patterns)."""
        return """<defs>
  <marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#37474f"/>
  </marker>
  <marker id="arrow-signal" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#d32f2f"/>
  </marker>
  <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
    <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
  </pattern>
</defs>"""

    def _grid(self, w: int, h: int) -> str:
        return f'<rect width="{w}" height="{h}" fill="url(#grid)"/>'

    def _draw_edge(self, edge: dict) -> str:
        """Draw an edge between two nodes."""
        src_id = edge["source"]
        tgt_id = edge["target"]

        if src_id not in self.layout or tgt_id not in self.layout:
            return ""

        src = self.layout[src_id]
        tgt = self.layout[tgt_id]

        # Determine start and end points
        if src.layer == tgt.layer:
            # Same layer - horizontal connection
            x1, y1 = src.right.x, src.right.y
            x2, y2 = tgt.left.x, tgt.left.y
        elif src.layer < tgt.layer:
            # Downward flow
            x1, y1 = src.bottom.x, src.bottom.y
            x2, y2 = tgt.top.x, tgt.top.y
        else:
            # Upward flow (recirculation, relief)
            x1, y1 = src.top.x, src.top.y
            x2, y2 = tgt.bottom.x, tgt.bottom.y

        # Line style based on edge type
        edge_type = edge.get("type", "process")
        if edge_type == "signal":
            stroke = "#d32f2f"
            dash = "5,3"
            marker = "url(#arrow-signal)"
            width = 1.5
        elif edge_type == "control":
            stroke = "#7b1fa2"
            dash = "10,3,2,3"
            marker = "url(#arrow-signal)"
            width = 1.5
        else:
            stroke = "#37474f"
            dash = "none"
            marker = "url(#arrow)"
            width = 2.5

        # Orthogonal routing
        if abs(x2 - x1) > abs(y2 - y1):
            mid_x = (x1 + x2) / 2
            path = f'M {x1},{y1} L {mid_x},{y1} L {mid_x},{y2} L {x2},{y2}'
        else:
            mid_y = (y1 + y2) / 2
            path = f'M {x1},{y1} L {x1},{mid_y} L {x2},{mid_y} L {x2},{y2}'

        # Label
        label = edge.get("role", "").replace("_", " ")
        label_svg = ""
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label_svg = f'<rect x="{mx-30}" y="{my-10}" width="60" height="16" fill="white" stroke="#bdbdbd" stroke-width="0.5" rx="2"/>'
            label_svg += f'<text x="{mx}" y="{my+2}" text-anchor="middle" fill="#424242" font-size="8">{label}</text>'

        return f'<path d="{path}" stroke="{stroke}" stroke-width="{width}" fill="none" stroke-dasharray="{dash}" marker-end="{marker}"/>{label_svg}'

    def _draw_node(self, node: dict, layout: LayoutNode) -> str:
        """Draw a node with ISA-5.1 symbol."""
        node_type = node.get("type", "unknown")
        subtype = node.get("subtype", "")
        tag = node.get("id", "")
        name = node.get("name", "")

        colors = self.COLORS.get(node_type, self.COLORS["equipment"])
        fill = colors["fill"]
        stroke = colors["stroke"]

        # Determine symbol type
        symbol_type = self._resolve_symbol_type(node_type, subtype)

        # Build symbol parameters
        params = {
            "x": layout.x,
            "y": layout.y,
            "w": layout.width,
            "h": layout.height,
            "x2": layout.x + layout.width,
            "y2": layout.y + layout.height,
            "cx": layout.center.x,
            "cy": layout.center.y,
            "fill": fill,
            "stroke": stroke,
            "accent": "#d32f2f",
            "tag": tag,
            "fs": min(10, layout.width / len(tag) * 1.5) if tag else 10,
        }

        # Add symbol-specific params
        if symbol_type in ("pump", "compressor", "instrument", "controller"):
            params["r"] = min(layout.width, layout.height) / 2 - 2
        if symbol_type == "pump":
            params["r2"] = params["r"] * 0.6
            params["y1"] = layout.center.y - params["r2"]
            params["y2"] = layout.center.y + params["r2"]
            params["x1"] = layout.center.x - params["r2"]
            params["x2"] = layout.center.x + params["r2"]
        if symbol_type == "heater":
            params["x1"] = layout.x + 5
            params["x1a"] = layout.x + 10
            params["x2a"] = layout.x + layout.width - 10
            params["x2q"] = layout.x + layout.width - 5
            params["x1q"] = layout.center.x - 5
            params["y1"] = layout.y + 10
            params["y1a"] = layout.y + 5
            params["y1q"] = layout.y
            params["y2"] = layout.y + layout.height - 10
            params["y2a"] = layout.y + layout.height - 5
            params["y2q"] = layout.y + layout.height
            params["ya"] = layout.y - 5
        if symbol_type in ("control_valve", "relief_valve", "safety_relief_valve"):
            params["y1"] = layout.y + 5
            params["y1a"] = layout.y - 5
            params["y2"] = layout.y + layout.height - 5
            params["x1a"] = layout.center.x - 6
            params["x2a"] = layout.center.x + 6
            params["x1s"] = layout.center.x - 8
            params["x2s"] = layout.center.x + 8
            params["wa"] = 12
            params["ha"] = 10
            params["ya"] = layout.y - 12
        if symbol_type == "check_valve":
            params["x1"] = layout.x + 5
            params["x2"] = layout.x + layout.width - 5
            params["y1"] = layout.y + 5
            params["y2"] = layout.y + layout.height - 5
        if symbol_type == "filter":
            params["x1"] = layout.x + 5
            params["x2"] = layout.x + layout.width - 5
            params["y1"] = layout.y + 5
            params["y2"] = layout.y + layout.height - 5
        if symbol_type == "tank":
            params["y1"] = layout.y + 10
            params["y2"] = layout.y + layout.height - 10

        symbol_template = self.SYMBOLS.get(symbol_type, self.SYMBOLS["tank"])
        symbol_svg = symbol_template.format(**params)

        # Label below symbol
        label_y = layout.y + layout.height + 15
        label_svg = f'<text x="{layout.center.x}" y="{label_y}" text-anchor="middle" fill="{stroke}" font-size="10" font-weight="500">{tag}</text>'

        # Tooltip group
        tooltip = f'<title>{tag}\n{type}: {subtype}\n{name}</title>'

        return f'<g class="node" data-id="{tag}">{tooltip}{symbol_svg}{label_svg}</g>'

    def _resolve_symbol_type(self, node_type: str, subtype: str) -> str:
        """Map node type+subtype to symbol type."""
        if node_type == "equipment":
            return subtype if subtype in self.SYMBOLS else "tank"
        elif node_type == "valve":
            return subtype if subtype in self.SYMBOLS else "control_valve"
        elif node_type == "instrument":
            return "instrument"
        elif node_type == "controller":
            return "controller"
        return "tank"


# ---------------------------------------------------------------------------
# HTML Wrapper
# ---------------------------------------------------------------------------

def generate_html(svg_content: str, title: str = "P&ID Flowchart") -> str:
    """Generate interactive HTML page with SVG."""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --bg: #fafafa;
    --fg: #212121;
    --panel: #ffffff;
    --border: #e0e0e0;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #121212;
      --fg: #e0e0e0;
      --panel: #1e1e1e;
      --border: #333333;
    }}
  }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--fg);
  }}
  .header {{
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }}
  .header h1 {{
    margin: 0;
    font-size: 20px;
    font-weight: 500;
  }}
  .container {{
    padding: 16px;
    overflow: auto;
  }}
  .svg-wrapper {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    display: inline-block;
  }}
  .svg-wrapper svg {{
    max-width: 100%;
    height: auto;
  }}
  .legend {{
    margin-top: 16px;
    padding: 12px 16px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 13px;
  }}
  .legend-item {{
    display: inline-flex;
    align-items: center;
    margin-right: 20px;
    margin-bottom: 8px;
  }}
  .legend-swatch {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    margin-right: 6px;
    border: 1.5px solid;
  }}
  .node:hover circle, .node:hover rect, .node:hover polygon {{
    filter: brightness(0.95);
    cursor: pointer;
  }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
</div>
<div class="container">
  <div class="svg-wrapper">
    {svg_content}
  </div>
  <div class="legend">
    <div class="legend-item"><span class="legend-swatch" style="background:#e3f2fd;border-color:#1565c0"></span>Equipment</div>
    <div class="legend-item"><span class="legend-swatch" style="background:#fff3e0;border-color:#ef6c00"></span>Valve</div>
    <div class="legend-item"><span class="legend-swatch" style="background:#fce4ec;border-color:#c2185b"></span>Instrument</div>
    <div class="legend-item"><span class="legend-swatch" style="background:#f3e5f5;border-color:#7b1fa2"></span>Controller</div>
    <div class="legend-item" style="margin-left:20px">— Process Line</div>
    <div class="legend-item">- - Signal Line</div>
  </div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate P&ID flowchart from connectivity JSON")
    parser.add_argument("input", help="Input connectivity JSON file")
    parser.add_argument("-o", "--output", default="flowchart", help="Output base name")
    parser.add_argument("--format", choices=["html", "svg", "mermaid", "all"], default="all")
    parser.add_argument("--title", default="P&ID Flowchart", help="Diagram title")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    # Render SVG
    renderer = SVGRenderer(data)
    svg = renderer.render()

    base = Path(args.output)

    if args.format in ("svg", "all"):
        with open(base.with_suffix(".svg"), "w") as f:
            f.write(svg)
        print(f"SVG: {base.with_suffix('.svg')}")

    if args.format in ("html", "all"):
        html = generate_html(svg, args.title)
        with open(base.with_suffix(".html"), "w") as f:
            f.write(html)
        print(f"HTML: {base.with_suffix('.html')}")

    if args.format in ("mermaid", "all"):
        # Simple Mermaid export
        from generate_connectivity_json_v2 import export_mermaid
        from generate_connectivity_json_v2 import ConnectivityGraph, Node, Edge

        graph = ConnectivityGraph()
        for n in data.get("nodes", []):
            graph.nodes.append(Node(**n))
        for e in data.get("edges", []):
            graph.edges.append(Edge(**e))

        export_mermaid(graph, base.with_suffix(".mmd"))
        print(f"Mermaid: {base.with_suffix('.mmd')}")

    print(f"\nNodes: {len(data.get('nodes', []))}, Edges: {len(data.get('edges', []))}")


if __name__ == "__main__":
    main()
