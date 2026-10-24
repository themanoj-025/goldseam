# Test Generator Prompt Template (v1)

Generate independent regression unit tests for the following SkillSpec.

SkillSpec:
{spec_summary}

Rules:
1. Derive tests exclusively from the specification examples, schema, and preconditions.
2. Author positive cases, negative cases, boundary cases, and Unicode edge cases.
3. Tests must be deterministic and run in an isolated Pytest sandbox.
