"""Durable, privacy-preserving run store for state machine execution history."""

import datetime
import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from goldseam.models.result import Attempt


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(description="Unique run identifier")
    created_at: str = Field(description="ISO-8601 creation timestamp")
    updated_at: str = Field(description="ISO-8601 last update timestamp")
    status: str = Field(default="INITIALIZED", description="Current execution state")
    source: str = Field(default="unknown", description="Ingested trace source")
    trace_hash: str = Field(default="", description="SHA-256 hash of the redacted trace")
    stage_data: dict[str, Any] = Field(
        default_factory=dict, description="Stage outputs and artifacts"
    )
    attempts: list[Attempt] = Field(
        default_factory=list, description="Compilation and repair attempts"
    )
    error: str | None = Field(default=None, description="Terminal failure or blocker explanation")


class RunStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        return self.root_dir / run_id

    def create_run(self, run_id: str | None = None, source: str = "unknown") -> RunRecord:
        rid = run_id or f"run_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.UTC).isoformat()
        record = RunRecord(
            run_id=rid,
            created_at=now,
            updated_at=now,
            status="INITIALIZED",
            source=source,
        )
        self.save_run(record)
        return record

    def save_run(self, record: RunRecord) -> None:
        run_dir = self._run_dir(record.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        record.updated_at = datetime.datetime.now(datetime.UTC).isoformat()

        # Write to temporary file then atomic rename
        tmp_file = run_dir / "run.json.tmp"
        target_file = run_dir / "run.json"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))
        tmp_file.replace(target_file)

    def get_run(self, run_id: str) -> RunRecord | None:
        target_file = self._run_dir(run_id) / "run.json"
        if not target_file.is_file():
            return None
        try:
            with open(target_file, encoding="utf-8") as f:
                data = json.load(f)
            return RunRecord(**data)
        except Exception:
            return None

    def list_runs(self) -> list[RunRecord]:
        runs: list[RunRecord] = []
        if not self.root_dir.is_dir():
            return runs
        for child in self.root_dir.iterdir():
            if child.is_dir() and (child / "run.json").is_file():
                rec = self.get_run(child.name)
                if rec:
                    runs.append(rec)
        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs

    def prune_retention(self, max_age_days: int = 30, keep_max_runs: int = 100) -> int:
        """Prunes old runs to ensure privacy-preserving retention and bounded storage."""
        import shutil

        runs = self.list_runs()
        pruned_count = 0
        now = datetime.datetime.now(datetime.UTC)
        cutoff = now - datetime.timedelta(days=max_age_days)

        for i, rec in enumerate(runs):
            should_prune = False
            # Check maximum count ceiling
            if i >= keep_max_runs:
                should_prune = True
            else:
                # Check age
                try:
                    created_dt = datetime.datetime.fromisoformat(rec.created_at)
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=datetime.UTC)
                    if created_dt < cutoff:
                        should_prune = True
                except Exception:
                    pass

            if should_prune:
                run_dir = self._run_dir(rec.run_id)
                if run_dir.is_dir():
                    shutil.rmtree(run_dir, ignore_errors=True)
                    pruned_count += 1

        return pruned_count

