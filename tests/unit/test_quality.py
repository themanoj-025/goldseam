"""Unit tests for ClaimsAuditor and TriggerEvaluator."""

from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec
from goldseam.quality.claims_audit import ClaimsAuditor
from goldseam.quality.trigger_eval import TriggerEvaluator


def test_claims_auditor() -> None:
    tool = ToolSpec(
        name="parse_json",
        purpose="Parses json payload format.",
        input_schema={"type": "object"},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"raw": "{}"}, expected={}, should_fail=False),
            Example(inputs={"raw": "{\"a\": 1}"}, expected={"a": 1}, should_fail=False),
            Example(inputs={"raw": "bad"}, expected="err", should_fail=True),
        ],
    )
    spec = SkillSpec(
        slug="json-parser",
        description="Parses json data strings.",
        triggers=["parse json"],
        non_triggers=["parse xml"],
        tools=[tool],
    )

    auditor = ClaimsAuditor()
    passed, warnings = auditor.audit_claims(spec)
    assert passed
    assert len(warnings) == 0


def test_trigger_evaluator() -> None:
    tool = ToolSpec(
        name="dummy_tool",
        purpose="Dummy purpose.",
        input_schema={},
        output_schema={},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={}, expected=1, should_fail=False),
            Example(inputs={}, expected=2, should_fail=False),
            Example(inputs={}, expected=3, should_fail=True),
        ],
    )
    spec = SkillSpec(
        slug="dummy",
        description="Dummy description.",
        triggers=["decode unicode", "clean text"],
        non_triggers=["database migration", "network requests"],
        tools=[tool],
    )

    evaluator = TriggerEvaluator()
    positives = [
        "Please decode unicode characters in this log",
        "Clean text escapes from json",
    ]
    negatives = [
        "Migrate database schema to v2",
        "Make a network request to api endpoint",
        "Deploy kubernetes cluster",
    ]

    metrics = evaluator.evaluate_triggers(spec, positives, negatives)
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0
