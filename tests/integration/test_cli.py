"""Integration tests for the Goldseam CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from goldseam.cli import app
from goldseam.core.orchestrator import CompilationState
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.result import GateOutcome, GateResult
from goldseam.registry.packager import AtomicPackager, CollisionMode
from goldseam.telemetry.run_store import RunStore

runner = CliRunner()


@pytest.fixture
def temp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    lib_dir = tmp_path / "skills"
    run_dir = tmp_path / "runs"
    lib_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GOLDSEAM_LIBRARY_DIR", str(lib_dir))
    monkeypatch.setenv("GOLDSEAM_RUN_STORE_DIR", str(run_dir))
    return tmp_path


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "goldseam version" in result.stdout


def test_cli_doctor_json() -> None:
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "python" in data
    assert "docker" in data
    assert "directories" in data
    assert data["python"]["ok"] is True


def test_cli_init(temp_workspace: Path) -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Initialized Goldseam workspace" in result.stdout


def test_cli_build_dry_run(temp_workspace: Path) -> None:
    result = runner.invoke(
        app,
        [
            "build",
            "--need",
            "Need a safe tool to validate email addresses",
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "DONE"
    assert "spec" in data["stage_data"]
    assert "bundle" in data["stage_data"]


def test_cli_verify_and_tamper(temp_workspace: Path) -> None:
    lib = temp_workspace / "skills"
    packager = AtomicPackager(lib)
    bundle = GeneratedBundle(
        skill_slug="cli-verify-skill",
        files=[
            GeneratedFile(
                path="SKILL.md",
                content="---\nname: cli-verify-skill\ndescription: Test.\n---\n# Tool\n## When to Use\n## When Not to Use\n## Steps\n## Examples",
            ),
            GeneratedFile(path="scripts/tool.py", content="def do_work(): pass\n", is_executable=True),
        ],
    )
    gates = [GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)]

    dest = packager.package_and_install(
        bundle=bundle,
        gate_results=gates,
        trace_hash="a" * 64,
        policy_hash="b" * 64,
        collision_mode=CollisionMode.OVERWRITE,
    )

    # 1. Verify fresh install
    res_verify = runner.invoke(app, ["verify", str(dest), "--json"])
    assert res_verify.exit_code == 0
    out = json.loads(res_verify.stdout)
    assert out["valid"] is True
    assert len(out["discrepancies"]) == 0

    # 2. Tamper by changing one byte in scripts/tool.py
    tool_file = dest / "scripts" / "tool.py"
    with open(tool_file, "a", encoding="utf-8", newline="\n") as f:
        f.write("# tampered comment\n")

    # 3. Verify detects tamper
    res_tamper = runner.invoke(app, ["verify", str(dest), "--json"])
    assert res_tamper.exit_code == 1
    tamper_out = json.loads(res_tamper.stdout)
    assert tamper_out["valid"] is False
    assert any("tool.py" in d for d in tamper_out["discrepancies"])


def test_cli_list_show_remove(temp_workspace: Path) -> None:
    # Initially empty list
    res_empty = runner.invoke(app, ["list", "--json"])
    assert res_empty.exit_code == 0
    assert json.loads(res_empty.stdout) == []

    # Install a skill
    lib = temp_workspace / "skills"
    packager = AtomicPackager(lib)
    bundle = GeneratedBundle(
        skill_slug="test-item",
        files=[
            GeneratedFile(
                path="SKILL.md",
                content="---\nname: test-item\ndescription: A test item skill.\n---\n# Tool\n## When to Use\n## When Not to Use\n## Steps\n## Examples",
            ),
            GeneratedFile(path="scripts/main.py", content="def run(): return 1\n", is_executable=True),
        ],
    )
    gates = [GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)]
    packager.package_and_install(
        bundle=bundle,
        gate_results=gates,
        trace_hash="c" * 64,
        policy_hash="d" * 64,
        collision_mode=CollisionMode.OVERWRITE,
    )

    # List shows test-item
    res_list = runner.invoke(app, ["list", "--json"])
    assert res_list.exit_code == 0
    skills = json.loads(res_list.stdout)
    assert len(skills) == 1
    assert skills[0]["slug"] == "test-item"

    # Show displays metadata
    res_show = runner.invoke(app, ["show", "test-item"])
    assert res_show.exit_code == 0
    details = json.loads(res_show.stdout)
    assert details["slug"] == "test-item"

    # Remove
    res_remove = runner.invoke(app, ["remove", "test-item"])
    assert res_remove.exit_code == 0
    assert "Removed skill 'test-item'" in res_remove.stdout

    # Show non-existent
    res_none = runner.invoke(app, ["show", "test-item"])
    assert res_none.exit_code == 1


def test_cli_explain_and_review(temp_workspace: Path) -> None:
    store = RunStore(temp_workspace / "runs")
    rec = store.create_run(run_id="run-test-1234", source="unit_test")
    rec.status = CompilationState.REVIEW
    rec.stage_data = {
        "diagnosis": {"root_cause": "Missing JSON parser", "confidence": 0.95},
        "spec": {"slug": "json-parser-skill", "description": "Parses json"},
    }
    store.save_run(rec)

    # Review command
    res_rev = runner.invoke(app, ["review", "run-test-1234"])
    assert res_rev.exit_code == 0
    assert "json-parser-skill" in res_rev.stdout

    # Explain command
    res_exp = runner.invoke(app, ["explain", "run-test-1234"])
    assert res_exp.exit_code == 0
    data = json.loads(res_exp.stdout)
    assert data["root_cause"] == "Missing JSON parser"

    # Proposals command
    res_prop = runner.invoke(app, ["proposals"])
    assert res_prop.exit_code == 0
    assert "run-test-1234" in res_prop.stdout


def test_cli_learn(temp_workspace: Path) -> None:
    diff_file = temp_workspace / "patch.diff"
    diff_file.write_text("--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n", encoding="utf-8")

    res = runner.invoke(app, ["learn", "--from-diff", str(diff_file), "--why", "Update config value"])
    assert res.exit_code == 0
    assert "Learned from diff" in res.stdout


def test_cli_review_approve_and_reject(temp_workspace: Path) -> None:
    store = RunStore(temp_workspace / "runs")
    rec = store.create_run(run_id="run-review-app", source="test")
    rec.status = CompilationState.REVIEW
    rec.stage_data = {
        "spec": {"slug": "approved-skill", "description": "Auto approved", "tools": []},
        "bundle": {
            "skill_slug": "approved-skill",
            "files": [
                {"path": "SKILL.md", "content": "---\nname: approved-skill\ndescription: Test.\n---\n# T\n## When to use\n## When not to use\n## Preconditions\n## Steps\n## Examples\n## Failure modes\n## Safety notes\n", "is_executable": False},
                {"path": "scripts/tool.py", "content": "def run(): pass\n", "is_executable": True},
            ],
            "description": "Bundle",
        },
    }
    rec.trace_hash = "f" * 64
    store.save_run(rec)

    # 1. Test approve
    res_app = runner.invoke(app, ["review", "run-review-app", "--approve"])
    assert res_app.exit_code == 0
    assert "Approved and installed skill" in res_app.stdout
    assert (temp_workspace / "skills" / "approved-skill" / "SKILL.md").is_file()

    # 2. Test reject
    rec_rej = store.create_run(run_id="run-review-rej", source="test")
    rec_rej.status = CompilationState.REVIEW
    store.save_run(rec_rej)

    res_rej = runner.invoke(app, ["review", "run-review-rej", "--reject", "Contains insecure pattern"])
    assert res_rej.exit_code == 0
    assert "Proposal rejected" in res_rej.stdout
    updated_rec = store.get_run("run-review-rej")
    assert updated_rec is not None
    assert updated_rec.status == CompilationState.REJECTED


def test_cli_resume(temp_workspace: Path) -> None:
    store = RunStore(temp_workspace / "runs")
    rec = store.create_run(run_id="run-resume-1", source="test")
    rec.status = CompilationState.REVIEW
    rec.stage_data = {
        "spec": {"slug": "resumed-skill", "description": "Resumed test", "tools": []},
        "bundle": {
            "skill_slug": "resumed-skill",
            "files": [
                {"path": "SKILL.md", "content": "---\nname: resumed-skill\ndescription: Resumed.\n---\n# T\n## When to use\n## When not to use\n## Preconditions\n## Steps\n## Examples\n## Failure modes\n## Safety notes\n", "is_executable": False},
            ],
            "description": "Resumed",
        },
    }
    rec.trace_hash = "e" * 64
    store.save_run(rec)

    res = runner.invoke(app, ["resume", "run-resume-1", "--yes"])
    assert res.exit_code == 0
    assert "Resumed Run run-resume-1" in res.stdout
    assert (temp_workspace / "skills" / "resumed-skill" / "SKILL.md").is_file()


def test_cli_build_transcript_and_target_mcp(temp_workspace: Path) -> None:
    transcript_file = temp_workspace / "agent_session.jsonl"
    transcript_file.write_text(
        json.dumps({"type": "user", "content": "Parse this csv"}) + "\n" +
        json.dumps({"type": "tool_result", "content": "Error: delimiter ';' not supported", "is_error": True}) + "\n",
        encoding="utf-8",
    )

    res = runner.invoke(
        app,
        [
            "build",
            "--from-transcript",
            str(transcript_file),
            "--target",
            "both",
            "--dry-run",
            "--json",
        ],
    )
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["status"] == "DONE"
    files = data["stage_data"]["bundle_files"]
    assert any("mcp_server.py" in f for f in files)


def test_cli_hook_watch_improve(temp_workspace: Path) -> None:
    # 1. Hook
    res_hook = runner.invoke(app, ["hook", "--error", "TypeError: unsupported operand"])
    assert res_hook.exit_code == 0
    assert "Recorded failure event" in res_hook.stdout

    # 2. Watch
    res_watch = runner.invoke(app, ["watch", "--json"])
    assert res_watch.exit_code == 0
    clusters = json.loads(res_watch.stdout)
    assert "TypeError:" in clusters

    # 3. Improve
    # First install a skill
    lib = temp_workspace / "skills"
    packager = AtomicPackager(lib)
    bundle = GeneratedBundle(
        skill_slug="active-skill",
        files=[
            GeneratedFile(
                path="SKILL.md",
                content="---\nname: active-skill\ndescription: An active skill.\n---\n# T\n## When to use\n## When not to use\n## Preconditions\n## Steps\n## Examples\n## Failure modes\n## Safety notes\n",
            ),
        ],
    )
    packager.package_and_install(
        bundle=bundle,
        gate_results=[GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)],
        trace_hash="1" * 64,
        policy_hash="2" * 64,
        collision_mode=CollisionMode.OVERWRITE,
    )

    res_imp = runner.invoke(app, ["improve", "active-skill"])
    assert res_imp.exit_code == 0
    assert "Skill Improvement Analysis: active-skill" in res_imp.stdout

