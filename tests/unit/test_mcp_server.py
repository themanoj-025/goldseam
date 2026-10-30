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

    # 4. Propose skill candidate
    prop_res = server.propose_skill(input_text="Need a skill to parse semver strings")
    assert prop_res["status"] == "PROPOSED"
    assert prop_res["installed"] is False
    assert prop_res["review_required"] is True

    # 5. Rate limit test
    rate_limited_server = GoldseamMCPServer(config=config, max_proposals_per_hour=1)
    res1 = rate_limited_server.propose_skill("Need 1")
    assert res1["status"] == "PROPOSED"
    res2 = rate_limited_server.propose_skill("Need 2")
    assert res2["status"] == "RATE_LIMITED"
    assert "rate limit" in res2["error"].lower()

    # 6. Budget cap test
    budget_server = GoldseamMCPServer(config=config, max_budget_per_proposal=0.50)
    # temporarily set config budget_usd higher than cap
    budget_server.config.budget_usd = 1.00
    res3 = budget_server.propose_skill("Need 3")
    assert res3["status"] == "BUDGET_EXCEEDED"

