"""Plain text capability requirement ingest adapter."""

import hashlib
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


class PlainNeedAdapter(IngestAdapter):
    name = "plain_need"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input
        clean_text = text.replace("\r\n", "\n").strip()
        redacted_text, counts, flags = self.redactor.redact(clean_text)

        event = TraceEvent(
            index=0,
            kind=TraceEventKind.PROMPT,
            text=redacted_text,
        )

        sig_hash = hashlib.sha256(redacted_text.encode("utf-8")).hexdigest()[:12]
        error_signature = f"User Requirement: {redacted_text[:100]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=[event],
            error_signature=error_signature,
            redaction_counts=counts,
            injection_flags=flags,
            metadata={"type": "free_text_need"},
        )
