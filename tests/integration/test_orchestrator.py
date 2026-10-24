"""Integration tests for Orchestrator and durable state machine."""

from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState, Orchestrator
from goldseam.llm.fake import FakeLLMClient
from goldseam.sandbox.backends.local import LocalSubprocessRunner
from goldseam.telemetry.run_store import RunStore


def test_orchestrator_dry_run_flow(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs")
    lib = tmp_path / "skills"
    cfg = GoldseamConfig(run_store_dir=store.root_dir, library_dir=lib, allow_weak_sandbox=True)

    orch = Orchestrator(
        config=cfg,
        llm_client=FakeLLMClient(),
        sandbox_runner=LocalSubprocessRunner(allow_weak=True),
        run_store=store,
    )

    record = orch.run_compilation(
        raw_input="Error: UnicodeDecodeError: invalid continuation byte",
        source="terminal_log",
        dry_run=True,
    )

    assert record.status == CompilationState.DONE
    assert record.stage_data.get("dry_run") is True
    assert "spec" in record.stage_data
    assert "diagnosis" in record.stage_data


def test_orchestrator_fail_closed_sandbox(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs")
    lib = tmp_path / "skills"
    # Local runner without allow_weak must fail closed and produce BLOCKED
    runner = LocalSubprocessRunner(allow_weak=False)
    cfg = GoldseamConfig(run_store_dir=store.root_dir, library_dir=lib, allow_weak_sandbox=False)

    orch = Orchestrator(
        config=cfg,
        llm_client=FakeLLMClient(),
        sandbox_runner=runner,
        run_store=store,
    )

    record = orch.run_compilation(
        raw_input="Error: UnicodeDecodeError: invalid continuation byte",
        source="terminal_log",
        dry_run=False,
    )

    assert record.status == CompilationState.BLOCKED
    assert "unhardened" in (record.error or "")


def test_orchestrator_full_install_with_approval(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs")
    lib = tmp_path / "skills"
    cfg = GoldseamConfig(
        run_store_dir=store.root_dir,
        library_dir=lib,
        allow_weak_sandbox=True,
        auto_approve_low_risk=True,
    )

    orch = Orchestrator(
        config=cfg,
        llm_client=FakeLLMClient(),
        sandbox_runner=LocalSubprocessRunner(allow_weak=True),
        run_store=store,
    )

    record = orch.run_compilation(
        raw_input="Error: UnicodeDecodeError: invalid continuation byte",
        source="terminal_log",
        dry_run=False,
        auto_approve=True,
    )

    assert record.status == CompilationState.DONE
    installed_skill = lib / "unicode-normalizer"
    assert installed_skill.is_dir()
    assert (installed_skill / "SKILL.md").is_file()
    assert (installed_skill / "goldseam.manifest.json").is_file()
    assert (installed_skill / "provenance.json").is_file()
