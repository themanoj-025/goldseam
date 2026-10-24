"""Unit tests for AtomicPackager and collision handling."""

from pathlib import Path

import pytest

from goldseam.errors import PackagingError
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.result import GateOutcome, GateResult
from goldseam.registry.packager import AtomicPackager, CollisionMode


def test_atomic_packager_install_and_collision(tmp_path: Path) -> None:
    lib = tmp_path / "skills"
    packager = AtomicPackager(lib)

    bundle = GeneratedBundle(
        skill_slug="atomic-tool",
        files=[
            GeneratedFile(path="SKILL.md", content="# Atomic Skill"),
            GeneratedFile(path="scripts/main.py", content="print('hello')", is_executable=True),
        ],
    )
    gates = [GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)]

    # Initial install succeeds
    installed_dir = packager.package_and_install(
        bundle=bundle,
        gate_results=gates,
        trace_hash="a" * 64,
        policy_hash="b" * 64,
        collision_mode=CollisionMode.FAIL,
    )
    assert installed_dir.is_dir()
    assert (installed_dir / "provenance.json").is_file()

    # Reinstall with CollisionMode.FAIL raises PackagingError
    with pytest.raises(PackagingError, match="already exists"):
        packager.package_and_install(
            bundle=bundle,
            gate_results=gates,
            trace_hash="a" * 64,
            policy_hash="b" * 64,
            collision_mode=CollisionMode.FAIL,
        )

    # Reinstall with BACKUP_AND_REPLACE succeeds cleanly
    updated_bundle = GeneratedBundle(
        skill_slug="atomic-tool",
        files=[
            GeneratedFile(path="SKILL.md", content="# Atomic Skill V2"),
            GeneratedFile(path="scripts/main.py", content="print('v2')", is_executable=True),
        ],
    )
    reinstalled_dir = packager.package_and_install(
        bundle=updated_bundle,
        gate_results=gates,
        trace_hash="a" * 64,
        policy_hash="b" * 64,
        collision_mode=CollisionMode.BACKUP_AND_REPLACE,
    )
    assert (reinstalled_dir / "SKILL.md").read_text(encoding="utf-8") == "# Atomic Skill V2"
