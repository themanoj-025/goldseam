"""Integration tests for bounded self-repair engine and oscillation detection."""

import pytest

from goldseam.core.repair import RepairEngine
from goldseam.errors import OscillationError, RepairExhaustedError
from goldseam.llm.fake import FakeLLMClient
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.result import GateOutcome, GateResult
from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec


@pytest.fixture
def sample_spec() -> SkillSpec:
    tool = ToolSpec(
        name="test_tool",
        purpose="Test tool purpose.",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"text": "a"}, expected="a", should_fail=False),
            Example(inputs={"text": "b"}, expected="b", should_fail=False),
            Example(inputs={"text": None}, expected="err", should_fail=True),
        ],
    )
    return SkillSpec(
        slug="test-skill",
        description="Test skill description.",
        triggers=["test trigger"],
        non_triggers=["bad trigger"],
        tools=[tool],
    )


def test_repair_exhaustion(sample_spec: SkillSpec) -> None:
    engine = RepairEngine(FakeLLMClient(), max_iterations=2)
    bundle = GeneratedBundle(
        skill_slug="test-skill",
        files=[
            GeneratedFile(path="SKILL.md", content="# Skill"),
            GeneratedFile(path="scripts/test_tool.py", content="def test_tool(): pass"),
        ],
    )
    gate = GateResult(gate="test_gate", passed=False, outcome=GateOutcome.FAIL, evidence="assert False")

    # Attempt 1 succeeds in returning repaired bundle
    repaired_1 = engine.repair_bundle(sample_spec, bundle, [gate], attempt_number=1)
    assert len(repaired_1.files) == 2

    # Attempt 3 exceeds max_iterations=2 -> RepairExhaustedError
    with pytest.raises(RepairExhaustedError, match="Exhausted maximum repair iterations"):
        engine.repair_bundle(sample_spec, bundle, [gate], attempt_number=3)


def test_oscillation_detection(sample_spec: SkillSpec) -> None:
    engine = RepairEngine(FakeLLMClient(), max_iterations=5)
    bundle = GeneratedBundle(
        skill_slug="test-skill",
        files=[
            GeneratedFile(path="SKILL.md", content="# Skill"),
            GeneratedFile(path="scripts/test_tool.py", content="def test_tool(): pass"),
        ],
    )
    gate = GateResult(gate="test_gate", passed=False, outcome=GateOutcome.FAIL, evidence="Identical error signature")

    # First attempt records failure signature
    engine.repair_bundle(sample_spec, bundle, [gate], attempt_number=1)

    # Identical failure signature on second attempt triggers OscillationError
    with pytest.raises(OscillationError, match="Oscillation detected"):
        engine.repair_bundle(sample_spec, bundle, [gate], attempt_number=2)
