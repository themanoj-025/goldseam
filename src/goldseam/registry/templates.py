"""Templates and renderers for SKILL.md, manifests, and CLI tool wrappers."""

import json
from typing import Any

import yaml

from goldseam.models.spec import SkillSpec


def render_skill_md(spec: SkillSpec) -> str:
    """Renders a spec-pure SKILL.md document adhering strictly to agentskills.io format."""
    frontmatter_dict: dict[str, Any] = {
        "name": spec.slug,
        "description": spec.description,
        "license": spec.license,
        "compatibility": spec.compatibility,
    }

    yaml_block = yaml.dump(frontmatter_dict, sort_keys=False, allow_unicode=True).strip()

    triggers_md = "\n".join(f"- {t}" for t in spec.triggers)
    non_triggers_md = "\n".join(f"- {nt}" for nt in spec.non_triggers)

    all_preconditions: list[str] = []
    for tool in spec.tools:
        all_preconditions.extend(tool.preconditions)
    if not all_preconditions:
        all_preconditions = ["None"]
    preconditions_md = "\n".join(f"- {p}" for p in all_preconditions)

    examples_md_blocks: list[str] = []
    for tool in spec.tools:
        for ex in tool.examples:
            kind = "Negative / Error Case" if ex.should_fail else "Positive Case"
            examples_md_blocks.append(
                f"### {tool.name} ({kind})\n"
                f"{ex.description}\n"
                f"- **Input:** `{json.dumps(ex.inputs)}`\n"
                f"- **Expected:** `{json.dumps(ex.expected)}`"
            )
    examples_md = "\n\n".join(examples_md_blocks)

    tools_summary_md = "\n".join(
        f"- `{tool.name}`: {tool.purpose} (Side effects: {', '.join(s.value for s in tool.side_effects)})"
        for tool in spec.tools
    )

    risk_text = "Not assessed"
    if spec.risk_assessment:
        risk_text = f"{spec.risk_assessment.level.value} - {spec.risk_assessment.justification}"

    body = f"""# {spec.slug.replace("-", " ").title()}

## When to Use
{triggers_md}

## When Not to Use
{non_triggers_md}

## Preconditions
{preconditions_md}

## Steps
1. Inspect the input arguments against the schema constraints.
2. Execute the corresponding tool script in `scripts/`:
{tools_summary_md}
3. Verify the exit code and returned JSON output payload.

## Examples
{examples_md}

## Failure Modes
- Invalid input schemas trigger a non-zero exit code with diagnostic JSON error on stderr.
- Precondition violations report descriptive failure reasons.

## Safety Notes
- Computed Risk Level: {risk_text}
- Sandboxing: Execution is strictly confined to unprivileged container environments.
- Ambient Network Access: Prohibited.
"""

    return f"---\n{yaml_block}\n---\n\n{body}"


def render_manifest(spec: SkillSpec) -> str:
    """Renders the comprehensive goldseam.manifest.json containing technical contracts."""
    data = {
        "$schema": "https://goldseam.local/schemas/manifest-v1.json",
        "name": spec.slug,
        "description": spec.description,
        "license": spec.license,
        "compatibility": spec.compatibility,
        "risk_assessment": spec.risk_assessment.model_dump() if spec.risk_assessment else None,
        "tools": [
            {
                "name": t.name,
                "purpose": t.purpose,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
                "side_effects": [s.value for s in t.side_effects],
                "allowed_imports": t.allowed_imports,
                "preconditions": t.preconditions,
                "examples_count": len(t.examples),
            }
            for t in spec.tools
        ],
        "replay_oracle_available": spec.replay_oracle is not None,
    }
    return json.dumps(data, indent=2)
