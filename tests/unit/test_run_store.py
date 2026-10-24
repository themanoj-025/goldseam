"""Unit tests for RunStore persistence and retrieval."""

from pathlib import Path

from goldseam.models.result import Attempt, GateOutcome, GateResult
from goldseam.telemetry.run_store import RunStore


def test_run_store_lifecycle(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run = store.create_run(source="test_trace")
    assert run.run_id.startswith("run_")
    assert run.source == "test_trace"

    # Add attempt
    gate = GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)
    attempt = Attempt(
        attempt_number=1,
        bundle_hash="c" * 64,
        gate_results=[gate],
        token_usage={"prompt": 100, "completion": 50},
        cost_usd=0.002,
        passed=True,
    )
    run.attempts.append(attempt)
    run.status = "SUCCESS"
    store.save_run(run)

    # Retrieve run
    fetched = store.get_run(run.run_id)
    assert fetched is not None
    assert fetched.status == "SUCCESS"
    assert len(fetched.attempts) == 1
    assert fetched.attempts[0].bundle_hash == "c" * 64

    # List runs
    all_runs = store.list_runs()
    assert len(all_runs) == 1
    assert all_runs[0].run_id == run.run_id
