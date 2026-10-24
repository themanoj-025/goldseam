"""Background watcher clustering recurring failures and generating proposals."""

import json
from collections import defaultdict
from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import Orchestrator
from goldseam.telemetry.run_store import RunRecord


class TelemetryWatcher:
    """Monitors telemetry spools, clusters recurring failures, and generates review-only proposals."""

    def __init__(self, spool_file: Path | None = None, config: GoldseamConfig | None = None) -> None:
        self.config = config or GoldseamConfig.load()
        self.spool_file = spool_file or (self.config.run_store_dir / "hook_spool.jsonl")

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

    def generate_proposals(self, min_occurrences: int = 2) -> list[RunRecord]:
        """Clusters recurring failures meeting recurrence threshold and generates review-only proposals."""
        clusters = self.cluster_failures()
        proposals: list[RunRecord] = []
        orch = Orchestrator(config=self.config)

        for sig, events in clusters.items():
            if len(events) >= min_occurrences:
                sample_error = str(events[0].get("error_text", ""))
                synthesis_prompt = (
                    f"Recurring agent error cluster ({len(events)} occurrences):\n{sample_error}"
                )
                record = orch.run_compilation(
                    raw_input=synthesis_prompt,
                    source=f"watcher_cluster_{sig}",
                    dry_run=True,
                    auto_approve=False,
                )
                proposals.append(record)

        return proposals
