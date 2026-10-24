"""Unit tests for LocalSubprocessRunner and opt-in security boundary."""

import pytest

from goldseam.errors import SandboxBlockedError
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.result import GateOutcome
from goldseam.sandbox.backends.local import LocalSubprocessRunner
from goldseam.sandbox.temp_env import staging_environment


def test_local_runner_blocks_without_opt_in() -> None:
    runner = LocalSubprocessRunner(allow_weak=False)
    avail, reason = runner.is_available()
    assert not avail
    assert "requires explicit opt-in" in reason

    f1 = GeneratedFile(path="SKILL.md", content="# Skill")
    f2 = GeneratedFile(path="tests/test_dummy.py", content="def test_ok(): pass")
    bundle = GeneratedBundle(skill_slug="dummy", files=[f1, f2])

    with staging_environment(bundle) as stage_dir:
        with pytest.raises(SandboxBlockedError, match="unhardened"):
            runner.run(stage_dir)


def test_local_runner_executes_with_opt_in() -> None:
    runner = LocalSubprocessRunner(allow_weak=True)
    avail, _ = runner.is_available()
    assert avail

    f1 = GeneratedFile(path="SKILL.md", content="# Skill")
    f2 = GeneratedFile(path="scripts/calc.py", content="def add(a, b): return a + b")
    f3 = GeneratedFile(
        path="tests/test_calc.py",
        content="from scripts.calc import add\ndef test_add(): assert add(2, 3) == 5\n",
    )
    bundle = GeneratedBundle(skill_slug="calc", files=[f1, f2, f3])

    with staging_environment(bundle) as stage_dir:
        result = runner.run(stage_dir)
        assert result.exit_code == 0
        assert result.outcome == GateOutcome.PASS
        assert not result.isolated  # Must be explicitly marked unhardened
