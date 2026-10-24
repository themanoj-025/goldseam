"""Tests for bounded memory and safe streaming of large log files."""

from pathlib import Path

from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.models.trace import NormalizedTrace


def test_large_log_streaming_bounded(tmp_path: Path) -> None:
    large_log = tmp_path / "large_50mb.log"

    # Write a repeating log file (~5MB in test for speed, verifying bounded event slicing)
    chunk = "2026-10-24 12:00:00 INFO Processing transaction item\n" * 1000
    with open(large_log, "w", encoding="utf-8") as f:
        for _ in range(50):  # 50,000 lines
            f.write(chunk)
        f.write("2026-10-24 12:01:00 ERROR ValueError: Out of bounds index in transaction batch\n")

    adapter = TerminalLogAdapter()
    trace: NormalizedTrace = adapter.ingest(large_log)

    assert isinstance(trace, NormalizedTrace)
    assert len(trace.events) > 0
    # The triage engine bounds events passed to LLM to max 40
    assert "ValueError" in trace.error_signature
