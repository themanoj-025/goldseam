"""Unit tests for telemetry hook, privacy redactor, and watcher."""

import json
from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.telemetry.hook import TelemetryHook
from goldseam.telemetry.run_store import RunStore
from goldseam.telemetry.watcher import TelemetryWatcher


def test_telemetry_hook_redaction(tmp_path: Path) -> None:
    spool_file = tmp_path / "spool.jsonl"
    hook = TelemetryHook(spool_file=spool_file)

    # Ingest error containing raw API key and email
    raw_error = "Traceback failed with secret sk-1234567890abcdef1234567890 and admin@example.com"
    context = {"user_email": "developer@corp.com", "code": 500}

    hook.record_failure(raw_error, context=context)

    assert spool_file.is_file()
    lines = spool_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    # Verify no raw secrets leaked
    assert "sk-1234567890abcdef1234567890" not in entry["error_text"]
    assert "admin@example.com" not in entry["error_text"]
    assert "developer@corp.com" not in str(entry["context"])
    assert "[REDACTED_API_KEY_1]" in entry["error_text"]
    assert "[REDACTED_EMAIL_" in entry["error_text"]
    assert entry["redaction_counts"]["API_KEY"] == 1


def test_telemetry_watcher_clustering(tmp_path: Path) -> None:
    spool_file = tmp_path / "spool.jsonl"
    hook = TelemetryHook(spool_file=spool_file)

    hook.record_failure("ValueError: Invalid phone format +123")
    hook.record_failure("ValueError: Invalid phone format +456")
    hook.record_failure("KeyError: missing 'id' key in response")

    watcher = TelemetryWatcher(spool_file=spool_file)
    clusters = watcher.cluster_failures()

    assert "ValueError:" in clusters
    assert len(clusters["ValueError:"]) == 2
    assert "KeyError:" in clusters
    assert len(clusters["KeyError:"]) == 1


def test_telemetry_watcher_generate_proposals(tmp_path: Path) -> None:
    spool_file = tmp_path / "spool.jsonl"
    hook = TelemetryHook(spool_file=spool_file)

    # Add 2 occurrences of ValueError to meet the min_occurrences threshold
    hook.record_failure("ValueError: invalid date string format '2026/13/45'")
    hook.record_failure("ValueError: invalid date string format '2026/02/30'")

    cfg = GoldseamConfig.load(overrides={"library_dir": tmp_path / "lib", "run_store_dir": tmp_path / "runs"})
    watcher = TelemetryWatcher(spool_file=spool_file, config=cfg)

    proposals = watcher.generate_proposals(min_occurrences=2)
    assert len(proposals) == 1
    # Check proposal was synthesized without direct installation into library
    assert proposals[0].stage_data.get("dry_run") is True or proposals[0].status == "REVIEW"
    lib_dir = tmp_path / "lib"
    assert not lib_dir.is_dir() or len(list(lib_dir.iterdir())) == 0



def test_run_store_prune_retention(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs")

    # Create 5 runs
    for i in range(5):
        store.create_run(run_id=f"run_test_{i}")

    assert len(store.list_runs()) == 5

    # Prune keeping max 2 runs
    pruned = store.prune_retention(max_age_days=365, keep_max_runs=2)
    assert pruned == 3
    assert len(store.list_runs()) == 2
