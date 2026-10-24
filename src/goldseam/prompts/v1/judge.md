# Advisory Judge Prompt Template (v1)

Perform an advisory evaluation on the generated skill candidate.

SkillSpec:
{spec_summary}

Generated Bundle:
{bundle_summary}

Audit:
1. Does the skill description promise capabilities that lack corresponding tests?
2. Are error messages actionable and clean?
3. Note: This judge is purely advisory; deterministic static and sandbox gates have final authority.
