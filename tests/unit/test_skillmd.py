"""Unit tests for SKILL.md linter, parser, and template renderers."""

from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec
from goldseam.registry.templates import render_manifest, render_skill_md
from goldseam.security.skillmd_lint import lint_skill_md, parse_skill_md


def test_parse_and_lint_valid_skillmd() -> None:
    content = """---
name: sample-skill
description: A verified test skill for normalizing data.
license: Apache-2.0
compatibility: Python >=3.11
---

# Sample Skill

## When to Use
- When inputs contain raw data

## When Not to Use
- When data is already cleaned

## Steps
1. Run tool script

## Examples
- Example 1
"""
    data, body = parse_skill_md(content)
    assert data["name"] == "sample-skill"
    assert "When to Use" in body

    violations = lint_skill_md(content, expected_slug="sample-skill")
    assert len(violations) == 0


def test_lint_catches_invalid_frontmatter() -> None:
    # 1. Non-standard tools field in frontmatter
    bad_content = """---
name: bad-skill
description: A bad skill.
tools:
  - my_tool
---

# Body
## When to Use
## When Not to Use
## Steps
## Examples
"""
    violations = lint_skill_md(bad_content)
    assert any("Non-standard fields" in v for v in violations)

    # 2. Uppercase name
    bad_name_content = """---
name: BadSkill
description: Valid description.
---
# Body
## When to Use
## When Not to Use
## Steps
## Examples
"""
    violations = lint_skill_md(bad_name_content)
    assert any("must contain only lowercase" in v for v in violations)


def test_render_skill_md_and_manifest() -> None:
    tool = ToolSpec(
        name="clean_data",
        purpose="Cleans unstructured data.",
        input_schema={"type": "object"},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"x": 1}, expected="1", should_fail=False),
            Example(inputs={"x": 2}, expected="2", should_fail=False),
            Example(inputs={"x": -1}, expected="ERR", should_fail=True),
        ],
    )
    spec = SkillSpec(
        slug="data-cleaner",
        description="Clean unstructured data streams into normalized formats.",
        triggers=["clean data", "unstructured raw data"],
        non_triggers=["database migrations"],
        tools=[tool],
    )

    rendered_md = render_skill_md(spec)
    assert "name: data-cleaner" in rendered_md
    violations = lint_skill_md(rendered_md, expected_slug="data-cleaner")
    assert len(violations) == 0

    manifest = render_manifest(spec)
    assert '"name": "data-cleaner"' in manifest
    assert '"replay_oracle_available": false' in manifest
