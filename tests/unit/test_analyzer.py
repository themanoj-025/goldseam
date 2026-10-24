"""Unit tests for TraceAnalyzer."""

from goldseam.core.analyzer import TraceAnalyzer
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


def test_trace_analyzer_telemetry() -> None:
    events = [
        TraceEvent(index=0, kind=TraceEventKind.COMMAND, text="docker run test"),
        TraceEvent(index=1, kind=TraceEventKind.STDERR, text="Traceback (most recent call last):\n  File 'a.py', line 5\nZeroDivisionError: division by zero"),
    ]
    trace = NormalizedTrace(
        source="test",
        events=events,
        error_signature="ZeroDivisionError [123456]",
    )

    analyzer = TraceAnalyzer()
    analysis = analyzer.analyze(trace)

    assert analysis.total_events == 2
    assert analysis.error_count == 1
    assert analysis.command_count == 1
    assert analysis.has_stack_trace is True
    assert "docker" in analysis.detected_technologies
