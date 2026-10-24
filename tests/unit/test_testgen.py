"""Unit tests for independent TestGenerator."""

from goldseam.core.testgen import TestGenerator
from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec


def test_independent_testgen() -> None:
    tool = ToolSpec(
        name="format_csv",
        purpose="Formats raw CSV rows.",
        input_schema={"type": "object", "properties": {"row": {"type": "string"}}},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"row": "1,2,3"}, expected="1,2,3", should_fail=False, description="Simple CSV row"),
            Example(inputs={"row": "a,b,c"}, expected="a,b,c", should_fail=False, description="Alphabetic CSV row"),
            Example(inputs={"row": None}, expected="error", should_fail=True, description="None row rejection"),
        ],
    )
    spec = SkillSpec(
        slug="csv-formatter",
        description="Formats CSV row strings.",
        triggers=["format csv"],
        non_triggers=["sql database"],
        tools=[tool],
    )

    testgen = TestGenerator()
    test_files = testgen.generate_tests_for_spec(spec)

    assert len(test_files) == 1
    tf = test_files[0]
    assert tf.path == "tests/test_format_csv.py"
    assert "test_format_csv_case_1" in tf.content
    assert "pytest.raises(Exception)" in tf.content

    # Verify deterministic test suite hashing
    suite_hash = TestGenerator.compute_test_suite_hash(test_files)
    assert len(suite_hash) == 64
