"""Pytest execution log ingest adapter."""

import hashlib
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


class PytestLogAdapter(IngestAdapter):
    name = "pytest_log"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input
        clean_text = text.replace("\r\n", "\n")
        redacted_text, counts, flags = self.redactor.redact(clean_text)

        lines = [line.strip() for line in redacted_text.splitlines() if line.strip()]
        events: list[TraceEvent] = []

        is_failure_section = False
        captured_error = ""

        for idx, line in enumerate(lines):
            if "=== FAILURES ===" in line:
                is_failure_section = True
            elif line.startswith("E   "):
                captured_error = line[4:].strip()

            kind = TraceEventKind.STDERR if (is_failure_section or line.startswith("FAILED")) else TraceEventKind.STDOUT
            exit_code = 1 if (is_failure_section or line.startswith("FAILED")) else None

            events.append(
                TraceEvent(
                    index=idx,
                    kind=kind,
                    text=line,
                    exit_code=exit_code,
                )
            )

        if not events:
            events.append(TraceEvent(index=0, kind=TraceEventKind.STDOUT, text="Empty pytest log"))

        sig = captured_error or (events[-1].text if events else "Pytest Failure")
        sig_hash = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:12]
        error_signature = f"{sig[:120]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=events,
            error_signature=error_signature,
            redaction_counts=counts,
            injection_flags=flags,
            metadata={"framework": "pytest"},
        )
