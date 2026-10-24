"""Unit tests for LibraryEvolutionManager: test preservation, upgrades, and retirement suggestions."""

from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.models.bundle import GeneratedBundle
from goldseam.models.spec import Example, SkillSpec, ToolSpec
from goldseam.registry.evolution import LibraryEvolutionManager


def test_library_evolution_retirements(tmp_path: Path) -> None:
    lib_dir = tmp_path / "skills"
    run_dir = tmp_path / "runs"
    lib_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy skill directory
    skill_a = lib_dir / "old-dormant-skill"
    skill_a.mkdir(parents=True, exist_ok=True)
    (skill_a / "SKILL.md").write_text("# Old Skill", encoding="utf-8")

    cfg = GoldseamConfig.load(overrides={"library_dir": lib_dir, "run_store_dir": run_dir})
    evo = LibraryEvolutionManager(cfg)

    suggestions = evo.suggest_retirements()
    assert len(suggestions) == 1
    assert suggestions[0]["slug"] == "old-dormant-skill"
    assert suggestions[0]["status"] == "UNVERIFIED_DORMANT"
    assert suggestions[0]["recommendation"] == "ARCHIVE"


def test_library_evolution_merge_and_upgrade(tmp_path: Path) -> None:
    lib_dir = tmp_path / "skills"
    skill_dir = lib_dir / "date-parser"
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Existing skill has manifest v0.1.0 and an existing test file
    (skill_dir / "goldseam.manifest.json").write_text(
        '{"version": "0.1.0", "slug": "date-parser"}', encoding="utf-8"
    )
    (tests_dir / "test_existing.py").write_text(
        "def test_old_regression(): assert True\n", encoding="utf-8"
    )

    cfg = GoldseamConfig.load(overrides={"library_dir": lib_dir})
    evo = LibraryEvolutionManager(cfg)

    from goldseam.models.spec import SideEffect

    spec = SkillSpec(
        slug="date-parser",
        description="Updated parser for dates",
        triggers=["parse date", "normalize date format"],
        non_triggers=["format currency", "send email"],
        tools=[
            ToolSpec(
                name="parse_date",
                purpose="Parses dates into normalized structured formats",
                side_effects=[SideEffect.NONE],
                input_schema={"type": "object", "properties": {"d": {"type": "string"}}},
                output_schema={"type": "object"},
                examples=[
                    Example(inputs={"d": "2026-01-01"}, expected={"year": 2026}),
                    Example(inputs={"d": "2026/01/01"}, expected={"year": 2026}),
                    Example(inputs={"d": "invalid"}, expected={"error": "invalid"}, should_fail=True),
                ],
            )
        ],
    )



    from goldseam.models.bundle import GeneratedFile

    new_bundle = GeneratedBundle(
        skill_slug="date-parser",
        files=[
            GeneratedFile(path="SKILL.md", content="# Date Parser"),
            GeneratedFile(path="goldseam.manifest.json", content='{"version": "0.1.0", "slug": "date-parser"}'),
            GeneratedFile(path="tests/test_new.py", content="def test_new_case(): assert 1 == 1\n"),
        ],
    )

    merged = evo.merge_or_upgrade("date-parser", spec, new_bundle)

    # 1. Previous regression test suite is preserved
    merged_map = {f.path: f.content for f in merged.files}
    assert "tests/prev_test_existing.py" in merged_map
    assert "test_old_regression" in merged_map["tests/prev_test_existing.py"]

    # 2. New tests exist
    assert "tests/test_new.py" in merged_map

    # 3. Version bumped from 0.1.0 to 0.1.1 (PATCH)
    manifest = merged_map["goldseam.manifest.json"]
    assert '"version": "0.1.1"' in manifest
    assert '"upgraded_from": "0.1.0"' in manifest

