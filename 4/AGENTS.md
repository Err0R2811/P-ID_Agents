# Agent Notes

## Project

`pid-agent-4` is a Python/uv CLI that processes vector P&ID PDFs:

- Validates the PDF is vector-based and reads page 1.
- Splits page 1 into three overlapping vertical bands (15% overlap by default).
- Renders each band to a PNG.
- Extracts words with bounding boxes from the source page.
- Calls OpenAI `gpt-4o` twice in parallel (Markdown summary + JSON connection list).
- Writes `output.md` and `output.json`.

## Common Commands

```bash
# Run tests
uv run pytest

# Run the CLI
export OPENAI_API_KEY="sk-..."
pid-agent-4 path/to/pid.pdf --output-dir ./out

# Split/extract only (no LLM call)
pid-agent-4 path/to/pid.pdf --splits-only

# Build the wheel
uv build --wheel
```

## Architecture

- `src/pid_agent_4/main.py` — CLI and pipeline orchestration.
- `src/pid_agent_4/config.py` — Pydantic settings with `PID_AGENT_` env prefix.
- `src/pid_agent_4/pdf.py` — PDF open, vector validation, dimensions.
- `src/pid_agent_4/splitter.py` — 3-way vertical split and PNG render.
- `src/pid_agent_4/extractor.py` — word extraction from the source page with split/overlap tagging.
- `src/pid_agent_4/llm.py` — OpenAI async client, prompt builders, parallel calls.
- `src/pid_agent_4/merger.py` — Markdown and JSON merge/dedup.
- `src/pid_agent_4/output.py` — write `.md` and `.json` files.

## Notes

- The overlap is interpreted as the **overlap region width** being 15% of the page width (each band extends `0.075W` beyond the nominal one-third boundary).
- Words are extracted from the **source page**, not from each split PDF, to avoid truncation of labels that cross a split boundary.
- The package uses `uv` for dependency management and `uv_build` as the build backend.
