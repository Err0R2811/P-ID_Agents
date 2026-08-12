# P&ID Extraction Pipeline v2.0

## Overview

This is an improved pipeline for extracting, analyzing, and visualizing Process & Instrumentation Diagrams (P&IDs) using AI vision models. The system converts P&ID images into structured data that LLMs can understand and reason about.

## Architecture

```
P&ID Image
    ↓
[adaptive_pid_recursive_extractor_v2.py]  ← Tile-based recursive extraction
    ↓
entities.json + llm_outputs.json
    ↓
[generate_connectivity_json_v2.py]          ← Build graph (nodes + edges)
    ↓
connectivity.json
    ↓
[generate_flowchart_v2.py]                  ← Interactive SVG/HTML flowchart
    ↓
flowchart.html + flowchart.svg
    ↓
[generate_report_v2.py]                     ← HAZOP study report
    ↓
HAZOP_Report.md + HAZOP_Report.html
```

## Improvements Over v1.0

### 1. adaptive_pid_recursive_extractor_v2.py

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Entity classification | Basic type | Full ISA-5.1 parsing (function, loop, suffix) |
| Bounding boxes | Simple overlap | IoU-based deduplication with confidence scoring |
| Connection inference | None | Spatial proximity + ISA relationship inference |
| Export formats | JSON only | JSON, CSV, GraphML, Markdown |
| Configuration | Hardcoded | Environment variable + CLI override |
| Data model | Flat dict | Typed dataclasses (Entity, Connection, TileResult) |
| Quality control | None | Confidence thresholds, validation |
| Prompt engineering | Generic | ISA-5.1 symbol guide with subtype classification |

**Key additions:**
- `Entity.isa_function`, `Entity.isa_loop`, `Entity.isa_suffix` — automatic ISA tag parsing
- `Connection.method` — tracks how connection was inferred (spatial, isa_loop, explicit)
- `Entity.confidence` — per-entity quality score
- `infer_connections()` — builds connection graph from spatial + ISA relationships
- `export_graphml()` — for import into Gephi, Cytoscape, etc.

### 2. generate_connectivity_json_v2.py

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Input source | Markdown regex | Direct JSON extraction data |
| ISA parsing | Manual patterns | Automatic `parse_isa_tag()` function |
| Subtype inference | Hardcoded | Dynamic from ISA function codes |
| Connection validation | None | `validate()` checks dangling edges, isolated nodes |
| Redundancy groups | Hardcoded | Auto-inferred from matching subtypes + loop numbers |
| Export formats | JSON only | JSON, YAML, Mermaid, Graphviz DOT |
| Graph queries | None | `get_neighbors()`, `get_outgoing()`, `get_incoming()` |

**Key additions:**
- `parse_isa_tag("TIC-005")` → `{"function": "TIC", "loop": "005", "suffix": ""}`
- `infer_subtype_from_tag("PDT-004", "instrument")` → `"differential_pressure"`
- `infer_measures_from_tag("TG-004")` → `"temperature"`
- `ConnectivityBuilder._infer_isa_connections()` — controller→valve, gauge→controller, switch→heater
- `ConnectivityBuilder._infer_redundancy_groups()` — auto-detects pump/filter/heater redundancy

### 3. generate_flowchart_v2.py

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Layout | Manual positions | Sugiyama automatic layered layout |
| Symbol rendering | Basic shapes | ISA-5.1 compliant symbols |
| Signal lines | Single style | Electrical (red dashed), pneumatic (blue), hydraulic (green) |
| Interactivity | None | Tooltips, click handlers, search |
| Responsive | No | Dark mode, zoom/pan ready |
| Export | HTML only | HTML, SVG, Mermaid |

**Key additions:**
- `SugiyamaLayout` — automatic node positioning using longest-path layering + barycenter ordering
- `SVGRenderer.SYMBOLS` — ISA-5.1 symbols: tank, pump, compressor, cooler, filter, heater, valves, instruments
- `SVGRenderer._draw_edge()` — orthogonal routing with proper line styles per edge type
- `generate_html()` — responsive wrapper with dark mode support

### 4. generate_report_v2.py

| Feature | v1.0 | v2.0 |
|---------|------|------|
| HAZOP generation | Template-based | Graph-driven node identification |
| Guide words | Static list | IEC 61882 standard with parameter mapping |
| Risk assessment | None | Severity × Likelihood matrix with auto-scoring |
| Action items | None | Auto-generated with risk-based prioritization |
| Deviation analysis | Manual | Auto-inferred from graph structure |
| Export | Markdown only | Markdown, HTML, JSON |

**Key additions:**
- `HAZOPNodeGenerator` — identifies study nodes from process graph
- `HAZOPDeviation` — complete deviation with cause, consequence, safeguards, risk score
- `_infer_cause()` / `_infer_consequence()` — context-aware based on node type and connections
- `_find_safeguards()` — extracts connected instruments as safeguards
- `_assess_risk()` — auto-severity/likelihood from consequence keywords and safeguard count

## Usage

### Step 1: Extract entities from P&ID image

```bash
export AGNES_API_KEY="your-api-key"
python adaptive_pid_recursive_extractor_v2.py 123_page-0001.jpg --output ./outputs
```

### Step 2: Generate connectivity graph

```bash
python generate_connectivity_json_v2.py ./outputs/123_page-0001.json --output connectivity --validate
```

### Step 3: Generate interactive flowchart

```bash
python generate_flowchart_v2.py connectivity.json --output flowchart --format html
```

### Step 4: Generate HAZOP report

```bash
python generate_report_v2.py connectivity.json --extraction ./outputs/123_page-0001.json --output ./reports --name "Lube Oil System"
```

## Data Model

### Entity (from extractor)
```json
{
  "tag": "TIC-005",
  "type": "controller",
  "subtype": "temperature_controller",
  "description": "Temperature indicating controller",
  "global_bbox": {"x0": 1200, "y0": 800, "x1": 1250, "y1": 850},
  "isa_function": "TIC",
  "isa_loop": "005",
  "isa_suffix": "",
  "confidence": 0.95,
  "connected_to": ["TCV-005", "TG-004"]
}
```

### Node (in connectivity graph)
```json
{
  "id": "TIC-005",
  "type": "controller",
  "subtype": "temperature_controller",
  "name": "Temperature indicating controller",
  "measures": "temperature",
  "isa_function": "TIC",
  "isa_loop": "005",
  "redundancy_group": ""
}
```

### Edge (connection)
```json
{
  "source": "TG-004",
  "target": "TIC-005",
  "type": "signal",
  "role": "measurement",
  "confidence": 0.95,
  "method": "isa_loop"
}
```

## File Structure

```
outputs/
├── adaptive_pid_recursive_extractor_v2.py   # Core extraction engine
├── generate_connectivity_json_v2.py         # Graph builder
├── generate_flowchart_v2.py                 # SVG/HTML renderer
├── generate_report_v2.py                    # HAZOP report generator
├── layout.md                                  # Component catalog (from analysis)
├── connectivity.md                          # Process connectivity (from analysis)
├── connectivity.json                        # Structured graph data
├── flowchart.svg                              # Static SVG diagram
├── flowchart.html                             # Interactive HTML diagram
└── README.md                                  # This file
```

## ISA-5.1 Tag Reference

| Function | Meaning | Examples |
|----------|---------|----------|
| P | Pressure | PI, PT, PC, PV, PS, PG |
| T | Temperature | TI, TT, TC, TV, TS, TG |
| L | Level | LI, LT, LC, LV, LS, LG |
| F | Flow | FI, FT, FC, FV, FS |
| PD | Differential Pressure | PDI, PDT, PDS, PD |
| A | Analysis | AI, AT, AC |
| HS | Hand Switch | HS-001 (manual control) |
| XS | Safety Interlock | XS-001 (safety system) |
| XL | Heater | XL-001 (tank heater) |
| K | Compressor | K-01 |
| TK | Tank | TK-001 |
| E | Filter/Exchanger | E-001 |

## License

MIT License — Use freely for industrial and academic purposes.
