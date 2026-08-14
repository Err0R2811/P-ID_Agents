# pid-agent-4

A Python/uv CLI pipeline that converts a vector P&ID PDF into a Markdown
summary and a JSON connection list.

## How it works

1. Validates that the PDF is vector-based and reads page 1.
2. Splits page 1 into three overlapping vertical bands (15% overlap by default).
3. Extracts all words and their bounding boxes from the source page.
4. Renders each split to a PNG.
5. Sends the three images plus the word list to two parallel OpenAI `gpt-4o` calls:
   - Markdown generation (equipment, instruments, lines, layout notes)
   - JSON generation (source/target connections with line numbers and tags)
6. Merges/deduplicates the results and writes `output.md` and `output.json`.

## Installation

```bash
uv venv
uv pip install -e .
```

## Usage

```bash
export OPENAI_API_KEY="sk-..."
pid-agent-4 path/to/pid.pdf --output-dir ./out --overlap 0.15 --dpi 150
```

To split and extract words without calling the LLM:

```bash
pid-agent-4 path/to/pid.pdf --splits-only
```

## Configuration

Settings can be passed as CLI flags or environment variables with the
`PID_AGENT_` prefix. Common options:

| CLI flag | Environment variable | Default |
|---|---|---|
| `--model` | `PID_AGENT_MODEL` | `gpt-4o` |
| `--output-dir` | `PID_AGENT_OUTPUT_DIR` | `./out` |
| `--overlap` | `PID_AGENT_OVERLAP` | `0.15` |
| `--dpi` | `PID_AGENT_DPI` | `150` |
| `--log-level` | `PID_AGENT_LOG_LEVEL` | `INFO` |

## Testing

```bash
uv run pytest
```
