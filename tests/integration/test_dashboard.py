"""Tests for visual terminal review dashboard and CLI integration."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console
from typer.testing import CliRunner

from goldseam.cli import app
from goldseam.core.orchestrator import CompilationState
from goldseam.models.result import Attempt, GateOutcome, GateResult
from goldseam.registry.dashboard import ReviewDashboard
from goldseam.telemetry.run_store import RunRecord, RunStore

runner = CliRunner()


def test_dashboard_render_overview() -> None:
    run = RunRecord(
        run_id="run-dash-123",
        created_at="2026-10-24T12:00:00Z",
        updated_at="2026-10-24T12:05:00Z",
        status=CompilationState.REVIEW,
        source="cli_need",
        stage_data={
            "spec": {"slug": "phone-validator", "description": "Validates E.164 phone numbers"},
            "bundle_files": [{"path": "SKILL.md", "is_executable": False, "content": "# Phone"}],
        },
        attempts=[
            Attempt(
                attempt_number=1,
                bundle_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                passed=True,
                gate_results=[
                    GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS, evidence="ok", duration_ms=12.5),
                    GateResult(gate="secrets", passed=True, outcome=GateOutcome.PASS, evidence="clean", duration_ms=5.0),
                ],
            )
        ],
    )


    console = MagicMock(spec=Console)
    dash = ReviewDashboard(console=console)
    panel = dash.render_overview(run)
    assert panel is not None
    dash.display(run)
    console.print.assert_called_once()


def test_cli_review_dashboard_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = tmp_path / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GOLDSEAM_RUN_STORE_DIR", str(run_dir))

    store = RunStore(run_dir)
    rec = store.create_run(run_id="run-cli-dash", source="test")
    rec.status = CompilationState.REVIEW
    rec.stage_data = {
        "spec": {"slug": "test-dash-skill", "description": "Dashboard test skill"},
        "bundle_files": ["SKILL.md", "goldseam.manifest.json"],
    }
    store.save_run(rec)

    res = runner.invoke(app, ["review", "run-cli-dash", "--dashboard"])
    assert res.exit_code == 0
    assert "Goldseam Human Review Dashboard" in res.stdout
    assert "test-dash-skill" in res.stdout
