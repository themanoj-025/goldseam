"""Unit tests for multi-format trace ingest adapters."""

from goldseam.ingest.git_diff import GitDiffAdapter
from goldseam.ingest.plain_need import PlainNeedAdapter
from goldseam.ingest.pytest_log import PytestLogAdapter
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.ingest.traceback_py import TracebackPyAdapter
from goldseam.models.trace import TraceEventKind


def test_terminal_log_adapter() -> None:
    adapter = TerminalLogAdapter()
    raw = "\x1b[31m$ git status\x1b[0m\r\nfatal: not a git repository\r\n"
    trace = adapter.ingest(raw)

    assert trace.source == "terminal_log"
    assert len(trace.events) == 2
    assert trace.events[0].kind == TraceEventKind.COMMAND
    assert trace.events[1].kind == TraceEventKind.STDERR
    assert "fatal: not a git repository" in trace.error_signature


def test_pytest_log_adapter() -> None:
    adapter = PytestLogAdapter()
    raw = """
============================= test session starts =============================
tests/test_app.py F
=== FAILURES ===
___ test_fail ___
> assert 1 == 2
E assert 1 == 2
FAILED tests/test_app.py::test_fail - assert 1 == 2
"""
    trace = adapter.ingest(raw)
    assert trace.source == "pytest_log"
    assert any(e.kind == TraceEventKind.STDERR for e in trace.events)
    assert "assert 1 == 2" in trace.error_signature


def test_traceback_py_adapter() -> None:
    adapter = TracebackPyAdapter()
    raw = """
Traceback (most recent call last):
  File "app.py", line 10, in <module>
    raise ValueError("Invalid unicode escape sequence")
ValueError: Invalid unicode escape sequence
"""
    trace = adapter.ingest(raw)
    assert trace.source == "traceback_py"
    assert "ValueError: Invalid unicode escape sequence" in trace.error_signature


def test_git_diff_adapter() -> None:
    adapter = GitDiffAdapter()
    raw = """
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
- old_code()
+ new_code()
"""
    trace = adapter.ingest(raw)
    assert trace.source == "git_diff"
    assert "app.py" in trace.metadata.get("modified_files", "")


def test_plain_need_adapter() -> None:
    adapter = PlainNeedAdapter()
    trace = adapter.ingest("Need a tool to parse CSV with irregular quote escapes.")
    assert trace.source == "plain_need"
    assert len(trace.events) == 1
    assert "CSV with irregular quote escapes" in trace.events[0].text
