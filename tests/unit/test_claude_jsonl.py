"""Unit tests for ClaudeCodeJsonlAdapter."""

from goldseam.ingest.claude_code_jsonl import ClaudeCodeJsonlAdapter
from goldseam.models.trace import TraceEventKind


def test_claude_code_jsonl_ingest() -> None:
    sample = (
        '{"type": "user", "content": "Extract emails from CSV"}\n'
        '{"type": "tool_call", "name": "shell", "args": {"cmd": "python parse.py"}}\n'
        '{"type": "tool_result", "content": "ValueError: malformed csv on row 5"}\n'
    )
    adapter = ClaudeCodeJsonlAdapter()
    trace = adapter.ingest(sample)

    assert trace.source == "claude_code_jsonl"
    assert len(trace.events) == 3
    assert trace.events[0].kind == TraceEventKind.PROMPT
    assert trace.events[1].kind == TraceEventKind.TOOL_CALL
    assert trace.events[2].kind == TraceEventKind.STDERR
    assert "ValueError" in trace.error_signature
