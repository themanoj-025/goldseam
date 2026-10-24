# Bounded Repair Engine Prompt Template (v1)

Repair the failing skill bundle using the structured gate failure packet.

Attempt: {attempt_number}
Failing Gates:
{gate_failures}

Guidelines:
1. Make the minimal necessary patch to satisfy the failing test or policy violation.
2. NEVER delete or weaken existing tests.
3. NEVER alter immutable replay anchor fixtures.
4. Keep all imports within the allowed policy.
