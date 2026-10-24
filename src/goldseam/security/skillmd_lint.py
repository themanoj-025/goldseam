"""Linter and parser for official Agent Skills specification (SKILL.md)."""

import re

import yaml

from goldseam.errors import SkillMdLintError

ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

NAME_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_skill_md(content: str) -> tuple[dict[str, object], str]:
    """
    Parses a SKILL.md document into (frontmatter_dict, markdown_body).
    Raises SkillMdLintError if delimiters or YAML are invalid.
    """
    if not content.startswith("---"):
        raise SkillMdLintError("SKILL.md must begin with YAML frontmatter delimiter '---'")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise SkillMdLintError("SKILL.md frontmatter is not properly terminated with '---'")

    yaml_block = parts[1]
    body = parts[2].lstrip("\r\n")

    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError as e:
        raise SkillMdLintError(f"YAML frontmatter parsing failed: {e}") from e

    if not isinstance(data, dict):
        raise SkillMdLintError("SKILL.md frontmatter must be a key-value dictionary")

    return data, body


def lint_skill_md(content: str, expected_slug: str | None = None) -> list[str]:
    """
    Validates SKILL.md content against the official Agent Skills specification.
    Returns a list of violation messages (empty if fully compliant).
    """
    violations: list[str] = []

    try:
        frontmatter, body = parse_skill_md(content)
    except SkillMdLintError as e:
        return [str(e)]

    # 1. Check required fields
    if "name" not in frontmatter or not isinstance(frontmatter["name"], str):
        violations.append("Missing required frontmatter string field: 'name'")
    else:
        name_val = frontmatter["name"]
        if len(name_val) > 64:
            violations.append(f"Field 'name' length ({len(name_val)}) exceeds 64 characters")
        if not NAME_REGEX.match(name_val):
            violations.append(
                f"Field 'name' ('{name_val}') must contain only lowercase alphanumeric and single hyphens"
            )
        if expected_slug and name_val != expected_slug:
            violations.append(
                f"Field 'name' ('{name_val}') does not match expected directory slug '{expected_slug}'"
            )

    if "description" not in frontmatter or not isinstance(frontmatter["description"], str):
        violations.append("Missing required frontmatter string field: 'description'")
    else:
        desc_val = frontmatter["description"].strip()
        if not desc_val:
            violations.append("Field 'description' must not be empty")
        elif len(desc_val) > 1024:
            violations.append(
                f"Field 'description' length ({len(desc_val)}) exceeds 1024 characters"
            )

    # 2. Check for disallowed non-standard fields in frontmatter
    disallowed_fields = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_FIELDS
    if disallowed_fields:
        violations.append(
            f"Non-standard fields found in SKILL.md frontmatter: {sorted(disallowed_fields)}. "
            "Technical metadata must be placed in goldseam.manifest.json or metadata field."
        )

    # 3. Check optional field types
    if "compatibility" in frontmatter:
        compat = frontmatter["compatibility"]
        if not isinstance(compat, str) or len(compat) > 500:
            violations.append("Field 'compatibility' must be a string <= 500 characters")

    if "metadata" in frontmatter and not isinstance(frontmatter["metadata"], dict):
        violations.append("Field 'metadata' must be a dictionary")

    # 4. Check markdown body structure
    required_sections = [
        "## When to Use",
        "## When Not to Use",
        "## Steps",
        "## Examples",
    ]
    for section in required_sections:
        if section.lower() not in body.lower():
            violations.append(
                f"SKILL.md body is missing recommended structural section: '{section}'"
            )

    return violations
