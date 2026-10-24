"""Background watcher clustering recurring failures and generating proposals."""

import json
from collections import defaultdict
from pathlib import Path

from goldseam.config import GoldseamConfig


class TelemetryWatcher:
    """Monitors telemetry spools and clusters recurring failures."""

    def __init__(self, spool_file: Path | None = None) -> None:
        cfg = GoldseamConfig.load()
        self.spool_file = spool_file or (cfg.run_store_dir / "hook_spool.jsonl")

    def cluster_failures(self) -> dict[str, list[dict[str, object]]]:
        if not self.spool_file.is_file():
            return {}

        clusters: dict[str, list[dict[str, object]]] = defaultdict(list)
        for line in self.spool_file.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                entry = json.loads(line_str)
                err = str(entry.get("error_text", ""))
                sig = err.split()[0] if err else "unknown"
                clusters[sig].append(entry)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return dict(clusters)
