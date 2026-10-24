"""Unit tests for LibraryIndex and tamper detection verification."""

from pathlib import Path

from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.result import GateOutcome, GateResult
from goldseam.registry.index import LibraryIndex
from goldseam.registry.packager import AtomicPackager, CollisionMode


def test_library_index_and_tamper_detection(tmp_path: Path) -> None:
    lib = tmp_path / "skills"
    packager = AtomicPackager(lib)
    index = LibraryIndex(lib)

    bundle = GeneratedBundle(
        skill_slug="tamper-check-tool",
        files=[
            GeneratedFile(path="SKILL.md", content="---\nname: tamper-check-tool\ndescription: Test.\n---\n# Tool\n## When to Use\n## When Not to Use\n## Steps\n## Examples"),
            GeneratedFile(path="scripts/calc.py", content="def calc(): return 100", is_executable=True),
        ],
    )
    gates = [GateResult(gate="schema", passed=True, outcome=GateOutcome.PASS)]

    installed = packager.package_and_install(
        bundle=bundle,
        gate_results=gates,
        trace_hash="a" * 64,
        policy_hash="b" * 64,
        collision_mode=CollisionMode.OVERWRITE,
    )

    # 1. Verification succeeds on fresh install
    valid, discrepancies = index.verify_skill(installed)
    assert valid, discrepancies
    assert len(discrepancies) == 0

    # 2. Modify one byte in scripts/calc.py
    with open(installed / "scripts" / "calc.py", "w", encoding="utf-8") as f:
        f.write("def calc(): return 101")  # altered single character

    valid_after_tamper, discrepancies_after = index.verify_skill(installed)
    assert not valid_after_tamper
    assert any("Integrity mismatch" in d for d in discrepancies_after)

    # 3. List skills
    skills = index.list_skills()
    assert len(skills) == 1
    assert skills[0]["slug"] == "tamper-check-tool"

    # 4. Remove skill
    removed = index.remove_skill("tamper-check-tool")
    assert removed
    assert len(index.list_skills()) == 0
