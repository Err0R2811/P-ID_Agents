# P&ID Agent Collection

A collection of three Piping & Instrumentation Diagram (P&ID) extraction and analysis agents. Each agent takes a different approach to turning P&ID images and PDFs into structured, machine-readable data, process graphs, and HAZOP-style reports.

## Repository Layout

```
.
├── 1/                              # Agent 1 — Image-based recursive extraction (v1)
│   └── P&ID_agent/
│       ├── adaptive_pid_recursive_extractor.py
│       ├── x.py
│       ├── y.ipynb
│       ├── Report.md               # Sample HAZOP report
│       ├── connectivity.md
│       ├── entities.json
│       ├── requirements.txt
│       ├── SKILL.md                # PFD/P&ID generator skill definition
│       └── outputs/                # Layout and summary artifacts
├── 2/                              # Agent 2 — Image-based extraction pipeline (v2)
│   └── P&ID_agent/
│       └── P&ID_agent/
│           └── PHA-Agent/
│               ├── adaptive_pid_recursive_extractor_v2.py
│               ├── generate_connectivity_json_v2.py
│               ├── generate_flowchart_v2.py
│               ├── generate_report_v2.py
│               ├── README.md
│               ├── requirements.txt
│               └── outputs/        # Flowcharts and HAZOP reports
└── 3(cursor)/                      # Agent 3 — PDF-based extraction system
    ├── main.py
    ├── requirements.txt
    ├── README.md
    ├── .cursor/agents/pid-extractor.md
    └── pid_extractor/              # Modular Python package
        ├── config.py
        ├── models.py
        ├── pdf/
        ├── detection/
        ├── graph/
        ├── llm/
        ├── pipeline/
        ├── validation/
        └── output/
```

## Agent 1 — Recursive P&ID Image Extractor (v1)

**Location:** `1/P&ID_agent/`

The first iteration uses a recursive, tile-based strategy to extract entities from a P&ID image.

- Splits a large P&ID image into tiles and runs an LLM vision model on each tile.
- Deduplicates entities across overlapping tiles.
- Saves every raw LLM response (`llm_outputs.json`) and the final deduplicated entity list (`entities.json`).
- Produces a `Report.md` HAZOP-style write-up and `outputs/layout.md` / `outputs/summary.md`.

### Quick start

```bash
cd 1/P&ID_agent
uv pip install -r requirements.txt
# Edit .env with your API key, then run the extractor or notebooks
python adaptive_pid_recursive_extractor.py
```

### Key files

| File | Purpose |
|------|---------|
| `adaptive_pid_recursive_extractor.py` | Core tile-based extractor |
| `x.py` / `y.ipynb` | Exploration and processing scripts |
| `Report.md` | Sample HAZOP report (Lube Oil System) |
| `SKILL.md` | PFD/P&ID generator skill definition |
| `outputs/` | Layout and summary markdown outputs |

## Agent 2 — P&ID Extraction Pipeline v2.0

**Location:** `2/P&ID_agent/P&ID_agent/PHA-Agent/`

A refined, four-stage pipeline that improves on v1 with ISA-5.1 parsing, graph construction, interactive flowcharts, and automated HAZOP reporting.

```
P&ID Image
    ↓
[adaptive_pid_recursive_extractor_v2.py]  ← Tile-based recursive extraction
    ↓
entities.json + llm_outputs.json
    ↓
[generate_connectivity_json_v2.py]        ← Build graph (nodes + edges)
    ↓
connectivity.json
    ↓
[generate_flowchart_v2.py]                ← Interactive SVG/HTML flowchart
    ↓
flowchart.html + flowchart.svg
    ↓
[generate_report_v2.py]                   ← HAZOP study report
    ↓
HAZOP_Report.md + HAZOP_Report.html
```

### Improvements over v1

- **ISA-5.1 parsing:** extracts `function`, `loop`, `suffix` from tags automatically.
- **IoU-based deduplication** with confidence scores.
- **Connection inference** from spatial proximity and ISA relationships.
- **Graph output** in JSON, YAML, Mermaid, and Graphviz DOT.
- **Interactive flowchart** with Sugiyama layout, ISA symbols, tooltips, and dark mode.
- **Automated HAZOP report** with IEC 61882 guide words and risk scoring.

### Quick start

```bash
cd 2/P&ID_agent/P&ID_agent/PHA-Agent
uv pip install -r requirements.txt
export AGNES_API_KEY="your-api-key"

python adaptive_pid_recursive_extractor_v2.py 123_page-0001.jpg --output ./outputs
python generate_connectivity_json_v2.py ./outputs/123_page-0001.json --output connectivity --validate
python generate_flowchart_v2.py connectivity.json --output flowchart --format html
python generate_report_v2.py connectivity.json --extraction ./outputs/123_page-0001.json --output ./reports --name "Lube Oil System"
```

### Key files

| File | Purpose |
|------|---------|
| `adaptive_pid_recursive_extractor_v2.py` | Improved tile-based extractor |
| `generate_connectivity_json_v2.py` | Graph builder with ISA parsing |
| `generate_flowchart_v2.py` | SVG/HTML flowchart generator |
| `generate_report_v2.py` | HAZOP report generator |
| `README.md` | Detailed v2.0 documentation |

## Agent 3 — P&ID PDF Extraction System

**Location:** `3(cursor)/`

A modular Python package that extracts P&IDs directly from PDFs using **PyMuPDF** and an optional **LLM vision API**. It produces structured JSON with equipment, instruments, valves, process lines, nodes, edges, and spatial relationships.

### Features

- Word, block, and span extraction with full bounding-box coordinates.
- 150 DPI page rendering for visual analysis.
- ISA-style tag search and entity detection.
- Graph building with nodes, edges, and relationship types.
- Cross-page tag linking.
- Confidence scoring and explicit uncertainty flagging.
- Three output modes: `SUMMARY`, `STRUCTURED` (JSON), and `GRAPH`.

### Quick start

```bash
cd 3(cursor)
uv pip install -r requirements.txt
cp .env.example .env
# Edit .env and set LLM_API_KEY

python main.py extract 123.pdf
python main.py summary 123.pdf
python main.py extract 123.pdf --mode graph -o output/graph.json
```

### Project structure

```
3(cursor)/
├── main.py                      # CLI entry point
├── pid_extractor/               # Extraction package
│   ├── pdf/                     # PyMuPDF layer
│   ├── detection/               # Entity and tag detection
│   ├── graph/                   # Nodes, edges, spatial reasoning
│   ├── llm/                     # Vision API client and prompts
│   ├── pipeline/                # End-to-end processor
│   ├── validation/              # Validation and confidence checks
│   └── output/                  # Output formatters
├── .cursor/agents/pid-extractor.md  # Cursor agent definition
└── output/                      # Generated results
```

### Key files

| File | Purpose |
|------|---------|
| `main.py` | CLI (`extract`, `summary`, `lookup`, `tags`) |
| `pid_extractor/pipeline/processor.py` | End-to-end pipeline orchestrator |
| `pid_extractor/pdf/extractor.py` | PyMuPDF text/layout/drawing extraction |
| `pid_extractor/llm/analyzer.py` | LLM vision analysis and merge |
| `pid_extractor/graph/edges.py` | Connection and relationship detection |
| `README.md` | Detailed usage and schema documentation |

## Common Concepts

All three agents share the goal of converting P&IDs into structured, actionable data:

| Concern | Agent 1 | Agent 2 | Agent 3 |
|---------|---------|---------|---------|
| Input | P&ID image | P&ID image | P&ID PDF |
| Extraction | Tile-based LLM vision | Tile-based LLM vision | PyMuPDF + optional LLM vision |
| ISA-5.1 parsing | Basic | Full | Yes |
| Graph output | No | Yes (JSON/YAML/DOT/Mermaid) | Yes (JSON/structured) |
| Flowchart | Basic | Interactive SVG/HTML | HTML/SVG/PDF |
| Report | HAZOP markdown | HAZOP markdown + HTML | Summary/structured |

## Configuration

Each agent has its own `requirements.txt` and environment setup. In general:

1. Install dependencies: `uv pip install -r requirements.txt`
2. Copy `.env.example` (where present) to `.env` and add your API key.
3. Run the relevant entry-point script or notebook.
