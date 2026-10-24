"""Terminal and console log ingest adapter."""

import hashlib
import re
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind

ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class TerminalLogAdapter(IngestAdapter):
    name = "terminal_log"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input

        # 1. Clean ANSI escape sequences and normalize line endings
        clean_text = ANSI_REGEX.sub("", text).replace("\r\n", "\n")

        # 2. Redact sensitive secrets and detect injection flags
        redacted_text, counts, flags = self.redactor.redact(clean_text)

        # 3. Construct chronological events
        lines = [line.strip() for line in redacted_text.splitlines() if line.strip()]
        events: list[TraceEvent] = []

        for idx, line in enumerate(lines):
            kind = TraceEventKind.STDOUT
            exit_code = None
            if line.startswith("$ ") or line.startswith("> "):
                kind = TraceEventKind.COMMAND
            elif any(err_kw in line.lower() for err_kw in ("error", "failed", "fatal", "exception")):
                kind = TraceEventKind.STDERR
                exit_code = 1

            events.append(
                TraceEvent(
                    index=idx,
                    kind=kind,
                    text=line,
                    exit_code=exit_code,
                )
            )

        if not events:
            events.append(TraceEvent(index=0, kind=TraceEventKind.STDOUT, text="Empty trace input"))

        # 4. Generate normalized error signature
        error_lines = [e.text for e in events if e.kind == TraceEventKind.STDERR]
        error_signature = error_lines[0] if error_lines else events[-1].text
        sig_hash = hashlib.sha256(error_signature.encode("utf-8")).hexdigest()[:12]
        error_signature = f"{error_signature[:120]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=events,
            error_signature=error_signature,
            redaction_counts=counts,
            injection_flags=flags,
            metadata={"total_lines": str(len(lines))},
        )
