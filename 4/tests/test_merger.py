"""Tests for output merging and deduplication."""

from __future__ import annotations

from pid_agent_4.merger import deduplicate_connections, merge_connections, merge_markdown
from pid_agent_4.models import PIDConnection


def test_merge_markdown_single():
    result = merge_markdown(["# Summary\n\nText"])
    assert result == "# Summary\n\nText"


def test_merge_markdown_multiple():
    result = merge_markdown(["# Page 1", "# Page 2"])
    assert "# Page 1" in result
    assert "# Page 2" in result
    assert "---" in result


def test_deduplicate_connections():
    connections = [
        PIDConnection(source_tag="P-101", target_tag="V-102", line_number="L-001"),
        PIDConnection(source_tag="P-101", target_tag="V-102", line_number="L-001"),
        PIDConnection(source_tag="P-101", target_tag="T-103", line_number="L-002"),
    ]

    deduped = deduplicate_connections(connections)
    assert len(deduped) == 2


def test_merge_connections_dedupes():
    connections = [
        PIDConnection(source_tag="P-101", target_tag="V-102", line_number="L-001"),
        PIDConnection(source_tag="P-101", target_tag="V-102", line_number="L-001"),
    ]
    merged = merge_connections(connections)
    assert len(merged) == 1
    assert merged[0].source_tag == "P-101"
