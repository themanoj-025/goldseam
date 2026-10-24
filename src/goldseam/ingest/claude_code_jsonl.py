"""Claude Code and AI Agent JSONL transcript ingest adapter."""

import hashlib
import json
from pathlib import Path

from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.redact import Redactor
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


class ClaudeCodeJsonlAdapter(IngestAdapter):
    name = "claude_code_jsonl"

    def __init__(self, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()

    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        text = raw_input.read_text(encoding="utf-8") if isinstance(raw_input, Path) else raw_input

        events: list[TraceEvent] = []
        event_idx = 0
        total_counts: dict[str, int] = {}
        all_flags: list[str] = []

        for line in text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
            except Exception:
                # Fallback to plain line
                data = {"content": line_str, "type": "raw"}

            msg_type = str(data.get("type", data.get("role", "unknown"))).lower()
            content = ""
            if "content" in data:
                content = str(data["content"])
            elif "text" in data:
                content = str(data["text"])
            elif "error" in data:
                content = str(data["error"])
            elif "message" in data:
                content = str(data["message"])
            else:
                content = json.dumps(data)

            # Redact content
            redacted_content, counts, flags = self.redactor.redact(content)
            for k, v in counts.items():
                total_counts[k] = total_counts.get(k, 0) + v
            for f in flags:
                if f not in all_flags:
                    all_flags.append(f)

            kind = TraceEventKind.STDOUT
            exit_code = None

            if "tool_result" in msg_type:
                if data.get("is_error") or any(err in redacted_content.lower() for err in ("error", "exception", "failed", "traceback", "valueerror")):
                    kind = TraceEventKind.STDERR
                    exit_code = 1
                else:
                    kind = TraceEventKind.STDOUT
            elif "error" in msg_type or "fail" in msg_type or "stderr" in msg_type:
                kind = TraceEventKind.STDERR
                exit_code = 1
            elif "tool" in msg_type or "command" in msg_type:
                kind = TraceEventKind.TOOL_CALL
            elif "user" in msg_type or "input" in msg_type:
                kind = TraceEventKind.PROMPT
            elif any(err in redacted_content.lower() for err in ("error", "exception", "failed", "traceback")):
                kind = TraceEventKind.STDERR
                exit_code = 1

            events.append(
                TraceEvent(
                    index=event_idx,
                    kind=kind,
                    text=redacted_content,
                    exit_code=exit_code,
                    metadata={"original_type": msg_type},
                )
            )
            event_idx += 1

        if not events:
            events.append(TraceEvent(index=0, kind=TraceEventKind.STDOUT, text="Empty JSONL transcript"))

        error_lines = [e.text for e in events if e.kind == TraceEventKind.STDERR]
        error_signature = error_lines[0] if error_lines else events[-1].text
        sig_hash = hashlib.sha256(error_signature.encode("utf-8")).hexdigest()[:12]
        error_signature = f"{error_signature[:120]} [{sig_hash}]"

        return NormalizedTrace(
            source=self.name,
            events=events,
            error_signature=error_signature,
            redaction_counts=total_counts,
            injection_flags=all_flags,
            metadata={"total_records": str(len(events))},
        )
