"""Integration tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

from pid_agent_4.main import main
from pid_agent_4.models import PIDConnection


def test_main_pipeline(sample_pdf_path: Path, tmp_path: Path):
    """Run the full CLI pipeline with a mocked LLM."""
    output_dir = tmp_path / "out"

    async def fake_llm(*args, **kwargs):
        return (
            "# P&ID Summary\n\nTest",
            [PIDConnection(source_tag="P-101", target_tag="V-102")],
        )

    with patch("pid_agent_4.main.run_llm_calls_with_partial", new=AsyncMock(side_effect=fake_llm)):
        rc = main([str(sample_pdf_path), f"--output-dir={output_dir}"])

    assert rc == 0
    assert (output_dir / "output.md").exists()
    assert (output_dir / "output.json").exists()
    assert (output_dir / "splits" / "page_1_part1.pdf").exists()

    json_text = (output_dir / "output.json").read_text()
    assert "P-101" in json_text
    assert "V-102" in json_text


def test_main_splits_only(sample_pdf_path: Path, tmp_path: Path):
    """Run the CLI in splits-only mode."""
    output_dir = tmp_path / "out2"
    rc = main([str(sample_pdf_path), f"--output-dir={output_dir}", "--splits-only"])
    assert rc == 0
    assert (output_dir / "splits" / "page_1_part1.pdf").exists()
    assert (output_dir / "splits" / "page_1_part1.png").exists()
