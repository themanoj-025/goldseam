"""Git diff correction ingest adapter."""

import hashlib
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


class GitDiffAdapter(IngestAdapter):
    name = "git_diff"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input
        clean_text = text.replace("\r\n", "\n")
        redacted_text, counts, flags = self.redactor.redact(clean_text)

        lines = [line.strip() for line in redacted_text.splitlines() if line.strip()]
        events: list[TraceEvent] = []

        modified_files: list[str] = []
        for idx, line in enumerate(lines):
            if line.startswith("+++ b/"):
                modified_files.append(line[6:])

            events.append(
                TraceEvent(
                    index=idx,
                    kind=TraceEventKind.DIFF,
                    text=line,
                )
            )

        if not events:
            events.append(TraceEvent(index=0, kind=TraceEventKind.DIFF, text="Empty git diff"))

        summary = f"Diff across: {', '.join(modified_files)}" if modified_files else "Git Diff Correction"
        sig_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest()[:12]
        error_signature = f"{summary[:120]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=events,
            error_signature=error_signature,
            redaction_counts=counts,
            injection_flags=flags,
            metadata={"modified_files": ", ".join(modified_files)},
        )
