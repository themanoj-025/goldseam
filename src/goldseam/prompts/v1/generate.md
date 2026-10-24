# Code Generator Prompt Template (v1)

Synthesize a spec-pure Agent Skill bundle matching the provided SkillSpec.

SkillSpec:
{spec_summary}

Rules:
1. Author standard `SKILL.md` with only standard Agent Skills frontmatter (`name`, `description`).
2. Provide deterministic pure Python tool functions in `scripts/`.
3. Do NOT import ambient or forbidden modules (`os`, `sys` whole module, `subprocess`, dynamic reflection).
4. Tools must read JSON args or stdin and emit deterministic JSON outputs.
