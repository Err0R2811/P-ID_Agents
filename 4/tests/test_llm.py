"""Tests for the LLM client and parsers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pid_agent_4.config import Settings
from pid_agent_4.exceptions import LLMCallError
from pid_agent_4.llm import _clean_json, _parse_json, run_llm_calls_with_partial
from pid_agent_4.models import ExtractedWord


def test_clean_json_removes_fences():
    assert _clean_json("```json\n[]\n```") == "[]"
    assert _clean_json("```\n[1, 2]\n```") == "[1, 2]"
    assert _clean_json('[{"a": 1}]') == '[{"a": 1}]'


def test_parse_json_returns_connections():
    data = [
        {
            "source_tag": "P-101",
            "target_tag": "V-102",
            "line_number": "L-001",
        }
    ]
    connections = _parse_json(json.dumps(data))
    assert len(connections) == 1
    assert connections[0].source_tag == "P-101"


def test_parse_json_rejects_non_array():
    with pytest.raises(LLMCallError):
        _parse_json('{"source_tag": "P-101"}')


def test_parse_json_skips_invalid_items():
    data = [
        {"source_tag": "P-101", "target_tag": "V-102"},
        {"bad_field": "no tags"},
    ]
    connections = _parse_json(json.dumps(data))
    assert len(connections) == 1


@pytest.mark.asyncio
async def test_run_llm_calls_parallel(tmp_path: Path):
    """Mock both LLM calls and verify parallel execution with valid responses."""
    settings = Settings(
        openai_api_key="sk-test",
        model="gpt-test",
        output_dir=tmp_path,
    )

    # Create a tiny fake PNG
    png = tmp_path / "part.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")

    words = [ExtractedWord(text="P-101", x0=0, y0=0, x1=10, y1=10, split_index=0)]

    json_text = json.dumps(
        [
            {
                "source_tag": "P-101",
                "target_tag": "V-102",
                "line_number": "L-001",
            }
        ]
    )

    markdown_text = "# Summary\n\nTest"

    async def fake_chat_completions(**kwargs):
        first_message = kwargs["messages"][0]["content"][0]["text"]
        if "JSON" in first_message:
            return MagicMock(
                choices=[MagicMock(message=MagicMock(content=json_text))]
            )
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content=markdown_text))]
        )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=fake_chat_completions)

    with patch("pid_agent_4.llm.openai.AsyncOpenAI", return_value=mock_client):
        markdown, connections = await run_llm_calls_with_partial([png], words, settings)

    assert mock_client.chat.completions.create.call_count == 2
    assert markdown == markdown_text
    assert len(connections) == 1
    assert connections[0].source_tag == "P-101"


@pytest.mark.asyncio
async def test_run_llm_calls_missing_key(tmp_path: Path):
    settings = Settings(openai_api_key="", output_dir=tmp_path)
    png = tmp_path / "part.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    words = [ExtractedWord(text="P-101", x0=0, y0=0, x1=10, y1=10, split_index=0)]

    with pytest.raises(LLMCallError):
        await run_llm_calls_with_partial([png], words, settings)
