"""Unit tests for CodeGenerator."""

from goldseam.core.generator import CodeGenerator
from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec


def test_generator_bundle_creation() -> None:
    tool = ToolSpec(
        name="clean_string",
        purpose="Cleans messy input strings.",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        allowed_imports=["re", "unicodedata"],
        examples=[
            Example(inputs={"text": "a"}, expected="a", should_fail=False),
            Example(inputs={"text": "b"}, expected="b", should_fail=False),
            Example(inputs={"text": None}, expected="err", should_fail=True),
        ],
    )
    spec = SkillSpec(
        slug="string-cleaner",
        description="Cleans messy string data into normalized format.",
        triggers=["clean string", "normalize text"],
        non_triggers=["database migration"],
        tools=[tool],
    )

    generator = CodeGenerator()
    bundle = generator.generate_bundle(spec)

    assert bundle.skill_slug == "string-cleaner"
    assert bundle.get_file("SKILL.md") is not None
    assert bundle.get_file("goldseam.manifest.json") is not None
    assert bundle.get_file("scripts/clean_string.py") is not None
    assert bundle.get_file("scripts/clean_string.py").is_executable  # type: ignore[union-attr]
