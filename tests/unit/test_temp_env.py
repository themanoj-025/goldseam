"""Unit tests for staging_environment context manager and path protection."""

from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.sandbox.temp_env import staging_environment


def test_staging_environment_lifecycle() -> None:
    f1 = GeneratedFile(path="SKILL.md", content="# Test Skill")
    f2 = GeneratedFile(path="scripts/main.py", content="print('hello')", is_executable=True)
    f3 = GeneratedFile(path="tests/test_main.py", content="def test(): assert 1 == 1")
    bundle = GeneratedBundle(skill_slug="test-tool", files=[f1, f2, f3])

    staging_path = None
    with staging_environment(bundle) as stage_dir:
        staging_path = stage_dir
        assert stage_dir.is_dir()
        assert (stage_dir / "SKILL.md").is_file()
        assert (stage_dir / "scripts" / "main.py").is_file()
        assert (stage_dir / "tests" / "test_main.py").is_file()

        with open(stage_dir / "SKILL.md", encoding="utf-8") as f:
            assert f.read() == "# Test Skill"

    # Directory must be cleaned up after context exit
    assert staging_path is not None
    assert not staging_path.exists()
