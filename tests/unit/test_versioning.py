"""Unit tests for SkillVersionComparator and semver bumping."""

from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec
from goldseam.registry.versioning import BumpType, SkillVersionComparator


def test_semver_parsing_and_bumping() -> None:
    comp = SkillVersionComparator()
    assert comp.bump_version("0.1.0", BumpType.PATCH) == "0.1.1"
    assert comp.bump_version("0.1.0", BumpType.MINOR) == "0.2.0"
    assert comp.bump_version("0.1.0", BumpType.MAJOR) == "1.0.0"

    t1 = ToolSpec(
        name="do_a",
        purpose="Perform action A on integer input",
        input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
        output_schema={"type": "object", "properties": {"result": {"type": "integer"}}},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"x": 1}, expected={"result": 1}, should_fail=False),
            Example(inputs={"x": 2}, expected={"result": 2}, should_fail=False),
            Example(inputs={"x": -1}, expected={"result": -1}, should_fail=True),
        ],
    )
    t2 = ToolSpec(
        name="do_b",
        purpose="Perform action B on generic input",
        input_schema={"type": "object", "properties": {"val": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"val": "ok"}, expected={"ok": True}, should_fail=False),
            Example(inputs={"val": "test"}, expected={"ok": True}, should_fail=False),
            Example(inputs={"val": ""}, expected={"ok": False}, should_fail=True),
        ],
    )

    spec_v1 = SkillSpec(slug="my-skill", description="Valid skill description v1", triggers=["a"], non_triggers=["b"], tools=[t1])
    spec_v2_minor = SkillSpec(slug="my-skill", description="Valid skill description v2", triggers=["a"], non_triggers=["b"], tools=[t1, t2])
    spec_v2_major = SkillSpec(slug="my-skill", description="Valid skill description v3", triggers=["a"], non_triggers=["b"], tools=[t2])

    assert comp.determine_bump(spec_v1, spec_v2_minor) == BumpType.MINOR
    assert comp.determine_bump(spec_v1, spec_v2_major) == BumpType.MAJOR
