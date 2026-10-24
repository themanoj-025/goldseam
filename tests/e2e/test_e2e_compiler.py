"""End-to-end full compilation workflow tests."""

from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState, Orchestrator
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.registry.index import LibraryIndex


def test_e2e_trace_to_verified_skill(tmp_path: Path) -> None:
    lib_dir = tmp_path / "skills"
    run_dir = tmp_path / "runs"
    lib_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    config = GoldseamConfig.load(
        overrides={
            "library_dir": lib_dir,
            "run_store_dir": run_dir,
            "sandbox_backend": "local",
            "allow_weak_sandbox": True,
            "auto_approve_low_risk": True,
        }
    )

    log_file = tmp_path / "failure.log"
    log_file.write_text(
        "Traceback (most recent call last):\n"
        "  File 'script.py', line 10, in <module>\n"
        "UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte\n",
        encoding="utf-8",
    )

    orchestrator = Orchestrator(config=config, ingest_adapter=TerminalLogAdapter())

    # 1. Run compilation
    record = orchestrator.run_compilation(
        raw_input=log_file,
        source="e2e_test",
        dry_run=False,
        auto_approve=True,
    )

    assert record.status in (CompilationState.PACKAGE, CompilationState.DONE)
    assert "spec" in record.stage_data
    slug = record.stage_data["spec"]["slug"]

    # 2. Verify skill was installed into library
    installed_dir = lib_dir / slug
    assert installed_dir.is_dir()
    assert (installed_dir / "SKILL.md").is_file()
    assert (installed_dir / "provenance.json").is_file()

    # 3. Verify provenance integrity
    index = LibraryIndex(lib_dir)
    valid, discrepancies = index.verify_skill(installed_dir)
    assert valid is True
    assert len(discrepancies) == 0

    # 4. Single-byte tampering detection
    script_files = list((installed_dir / "scripts").glob("*.py"))
    if script_files:
        target_script = script_files[0]
        with open(target_script, "a", encoding="utf-8", newline="\n") as f:
            f.write("# tampered single byte\n")

        valid_tampered, discrepancies_tampered = index.verify_skill(installed_dir)
        assert valid_tampered is False
        assert any("Integrity mismatch" in d for d in discrepancies_tampered)
