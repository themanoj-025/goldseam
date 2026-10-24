"""Fast, non-blocking telemetry hook for agent environments."""

import json
import time
from pathlib import Path
from typing import Any

from goldseam.config import GoldseamConfig


class TelemetryHook:
    """Non-blocking ingest spooling agent errors to a local queue."""

    def __init__(self, spool_file: Path | None = None) -> None:
        cfg = GoldseamConfig.load()
        self.spool_file = spool_file or (cfg.run_store_dir / "hook_spool.jsonl")
        self.spool_file.parent.mkdir(parents=True, exist_ok=True)

    def record_failure(self, error_text: str, context: dict[str, Any] | None = None) -> None:
        payload = {
            "timestamp": time.time(),
            "error_text": error_text,
            "context": context or {},
        }
        with open(self.spool_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
