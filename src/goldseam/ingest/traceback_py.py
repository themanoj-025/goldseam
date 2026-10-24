"""Python traceback ingest adapter."""

import hashlib
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


class TracebackPyAdapter(IngestAdapter):
    name = "traceback_py"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input
        clean_text = text.replace("\r\n", "\n")
        redacted_text, counts, flags = self.redactor.redact(clean_text)

        lines = [line.strip() for line in redacted_text.splitlines() if line.strip()]
        events: list[TraceEvent] = []

        last_error_line = ""
        for idx, line in enumerate(lines):
            kind = TraceEventKind.STDERR
            exit_code = 1
            if ":" in line and not line.startswith("File "):
                last_error_line = line

            events.append(
                TraceEvent(
                    index=idx,
                    kind=kind,
                    text=line,
                    exit_code=exit_code,
                )
            )

        if not events:
            events.append(TraceEvent(index=0, kind=TraceEventKind.STDERR, text="Empty traceback", exit_code=1))

        sig = last_error_line or events[-1].text
        sig_hash = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:12]
        error_signature = f"{sig[:120]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=events,
            error_signature=error_signature,
            redaction_counts=counts,
            injection_flags=flags,
            metadata={"type": "python_traceback"},
        )
