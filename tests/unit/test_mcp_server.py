"""Unit tests for GoldseamMCPServer proposal and verify operations."""

from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState
from goldseam.registry.mcp_server import GoldseamMCPServer
from goldseam.telemetry.run_store import RunStore


def test_mcp_proposal_server(tmp_path: Path) -> None:
    lib_dir = tmp_path / "skills"
    run_dir = tmp_path / "runs"
    lib_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    config = GoldseamConfig.load(
        overrides={
            "library_dir": lib_dir,
            "run_store_dir": run_dir,
        }
    )

    store = RunStore(run_dir)
    rec = store.create_run(run_id="run-mcp-1", source="agent_log")
    rec.status = CompilationState.REVIEW
    rec.stage_data = {
        "spec": {"slug": "mcp-candidate-skill", "description": "Candidate skill"},
        "diagnosis": {"root_cause": "Missing utility", "confidence": 0.95},
    }
    store.save_run(rec)

    server = GoldseamMCPServer(config=config)

    # 1. List proposals
    proposals = server.list_proposals()
    assert len(proposals) == 1
    assert proposals[0]["run_id"] == "run-mcp-1"
    assert proposals[0]["slug"] == "mcp-candidate-skill"

    # 2. Explain run
    explanation = server.explain_run("run-mcp-1")
    assert explanation is not None
    assert explanation["status"] == CompilationState.REVIEW
    assert explanation["diagnosis"]["root_cause"] == "Missing utility"

    # 3. Verify non-existent skill returns false
    ver_res = server.verify_skill("non-existent")
    assert ver_res["valid"] is False
