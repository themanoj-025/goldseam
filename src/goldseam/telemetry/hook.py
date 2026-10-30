"""Fast, non-blocking telemetry hook for agent environments with mandatory privacy redaction."""

import json
import time
from pathlib import Path
from typing import Any

from goldseam.config import GoldseamConfig
from goldseam.ingest.redact import Redactor


class TelemetryHook:
    """Non-blocking ingest spooling agent errors to a local queue with mandatory redaction."""

    def __init__(self, spool_file: Path | None = None) -> None:
        cfg = GoldseamConfig.load()
        self.spool_file = spool_file or (cfg.run_store_dir / "hook_spool.jsonl")
        self.spool_file.parent.mkdir(parents=True, exist_ok=True)
        self.redactor = Redactor()

    def record_failure(self, error_text: str, context: dict[str, Any] | None = None) -> None:
        """Redacts sensitive material and persists failure event to local spool."""
        redacted_error, counts, flags = self.redactor.redact(error_text)

        sanitized_context: dict[str, Any] = {}
        if context:
            for k, v in context.items():
                if isinstance(v, str):
                    redacted_v, _, _ = self.redactor.redact(v)
                    sanitized_context[k] = redacted_v
                else:
                    sanitized_context[k] = v

        payload = {
            "timestamp": time.time(),
            "error_text": redacted_error,
            "redaction_counts": counts,
            "injection_flags": flags,
            "context": sanitized_context,
        }
        with open(self.spool_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
