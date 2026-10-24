# SkillSpec Designer Prompt Template (v1)

Design a typed SkillSpec contract to solve the following diagnosed capability gap.

Diagnosis:
- Failure Class: {failure_class}
- Root Cause: {root_cause}
- Capability Gap: {capability_gap}

Requirements:
- Specify unique slug name (kebab-case)
- Meaningful trigger description (When to use / When not to use)
- Define tool specs with strict JSON Schema inputs and outputs
- Side effects must be explicitly declared (NONE, READ_WORKSPACE, WRITE_WORKSPACE)
- Include at least 3 examples with at least 1 negative (failing) example
