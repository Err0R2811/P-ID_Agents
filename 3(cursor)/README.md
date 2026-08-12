# P&ID PDF Extraction System

Extract, structure, and analyze **Piping & Instrumentation Diagrams (P&IDs)** from PDF files using PyMuPDF. Produces machine-readable JSON with equipment, instruments, valves, process lines, nodes, edges, and spatial relationships.

## Features

- **Word-level extraction** — `page.get_text("words")` with full coordinates
- **Layout extraction** — Block > Line > Span hierarchy with fonts and bboxes
- **P&ID text search** — ISA-style instrument codes, valve types, equipment tags
- **Page rendering** — 150 DPI images for visual symbol analysis
- **Entity detection** — Equipment, instruments, valves, lines, annotations
- **Graph building** — Nodes and edges with relationship types
- **Cross-page linking** — Match tags across pages
- **Confidence scoring** — 0.0–1.0 for all entities and relationships
- **No hallucination** — Uncertain items flagged explicitly
- **Three output modes** — SUMMARY, STRUCTURED (JSON), GRAPH

## Installation

```bash
uv pip install -r requirements.txt
cp .env.example .env   # then set LLM_API_KEY
```

## LLM Configuration

Analysis uses an **external LLM API** (OpenAI-compatible vision model), not the Cursor agent. Configure via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | Your API key (required for LLM analysis) |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API base URL (change for OpenRouter, DeepSeek, etc.) |
| `LLM_MODEL` | `gpt-4o` | Vision-capable model name |
| `LLM_ENABLED` | `true` | Set `false` to disable LLM and use PyMuPDF heuristics only |
| `LLM_TEMPERATURE` | `0.1` | Lower = more deterministic extraction |

The pipeline always runs PyMuPDF first (text, layout, coordinates), then sends the rendered page image + extracted text to the LLM for visual interpretation, entity association, and connection detection.

```bash
# With LLM (default when LLM_API_KEY is set)
python main.py extract diagram.pdf

# PyMuPDF only — no LLM API calls
python main.py extract diagram.pdf --no-llm
```

## Quick Start

```bash
# Full extraction to JSON
python main.py extract diagram.pdf

# Human-readable summary
python main.py summary diagram.pdf

# Graph output (nodes + edges only)
python main.py extract diagram.pdf --mode graph -o output/graph.json

# Single page
python main.py extract diagram.pdf --pages 3

# Look up equipment by tag
python main.py lookup diagram.pdf --tag P-101

# List all detected tags
python main.py tags diagram.pdf
```

## Python API

```python
from pid_extractor.pipeline.processor import PIDProcessor
from pid_extractor.config import PipelineConfig

config = PipelineConfig(dpi=150, pages=[1, 2, 3])
processor = PIDProcessor(config)
result = processor.process("diagram.pdf")

# Access entities
for entity in result.global_entities:
    print(f"{entity.tag} [{entity.type}] conf={entity.confidence}")

# Graph output
graph = result.to_graph()
print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
```

## Output Schema

```json
{
  "document": {"filename": "", "page_count": 0, "pages_processed": 0},
  "pages": [{
    "page_number": 1,
    "width": 0, "height": 0,
    "text": {"words": [], "blocks": []},
    "entities": [], "nodes": [], "edges": [],
    "lines": [], "annotations": []
  }],
  "global_entities": [],
  "global_connections": [],
  "uncertain_items": [],
  "validation": {"valid": true, "warnings": []}
}
```

## Entity Types

| Type | Subtypes | Examples |
|------|----------|----------|
| equipment | pump, compressor, tank, vessel, heat_exchanger, reactor | P-101, TK-201, E-301 |
| instrument | transmitter, indicator, controller | PT-101, FIC-201, TI-301 |
| valve | control_valve, pressure_safety, on_off | FCV-101, PSV-201, XV-301 |
| line | — | 2"-PL-101-001, L-101 |
| annotation | note, specification, unit | NOTE 1, PSIG |

## Relationship Types

- `connected_to` — Pipe/line connection
- `flows_to` — Flow direction
- `controlled_by` — Controller → valve
- `measured_by` — Transmitter → controller
- `continues_on_page` — Cross-page tag match
- `labeled_as` — Tag ↔ symbol association
- `nearby` — Spatial proximity (low confidence)

## Project Structure

```
PDF/
├── .cursor/agents/pid-extractor.md   # Cursor AI agent definition
├── main.py                           # CLI entry point
├── requirements.txt
├── pid_extractor/
│   ├── config.py                     # Patterns, thresholds, constants
│   ├── models.py                     # Data models and JSON schema
│   ├── pdf/
│   │   ├── extractor.py              # PyMuPDF word/layout/drawing extraction
│   │   ├── renderer.py               # Page rendering with cache
│   │   └── search.py                 # P&ID terminology search
│   ├── llm/
│   │   ├── client.py                 # OpenAI-compatible vision API client
│   │   ├── analyzer.py               # LLM page analysis + merge with PyMuPDF
│   │   └── prompts.py                # Anti-hallucination prompts
│   ├── detection/
│   │   ├── entities.py               # Entity detection pipeline
│   │   ├── tags.py                   # Tag parsing (P-101, FIC-201, etc.)
│   │   └── visual.py                 # Visual/drawing analysis
│   ├── graph/
│   │   ├── nodes.py                  # Node graph construction
│   │   ├── edges.py                  # Connection/relationship detection
│   │   └── spatial.py                # Spatial reasoning
│   ├── pipeline/
│   │   └── processor.py              # End-to-end orchestrator
│   ├── validation/
│   │   └── validator.py              # Result validation
│   └── output/
│       └── formatter.py              # SUMMARY/STRUCTURED/GRAPH output
└── output/                           # Default output directory
```

## Analysis Pipeline

```
PDF → PyMuPDF (text + layout + coords) → Page render (150 DPI)
    → LLM vision API (entities, associations, connections)
    → Merge + validate → Structured JSON
```

Use `--no-llm` for offline PyMuPDF-only extraction.

## Limitations

- **Scanned PDFs** — Falls back to visual-only analysis with reduced confidence
- **Symbol recognition** — Basic heuristics; complex symbols may be flagged uncertain
- **Connection inference** — Requires corroborating evidence; proximity alone is not sufficient
- **Standards** — Optimized for ISA-style tagging; custom formats may need config updates

## Confidence Guidelines

| Range | Meaning |
|-------|---------|
| 0.9–1.0 | High — text match with layout confirmation |
| 0.7–0.9 | Medium — text match, limited visual confirmation |
| 0.5–0.7 | Low — pattern match only |
| < 0.5 | Uncertain — flagged for human review |

## License

MIT
