# Triage Prompt Template (v1)

You are an expert diagnostic compiler for agentic AI systems.
Analyze the following normalized trace events to diagnose whether an engineering capability gap exists.

Trace Source: {source}
Normalized Error Signature: {signature}

Trace Events:
{events_summary}

Determine:
1. Taxonomic failure class
2. Technical root cause
3. Reusable capability gap
4. Verifiable evidence citations with event indices
5. Diagnostic confidence score [0.0 - 1.0]
6. Recommended route: SKILL, SCRIPT, MCP_TOOL, RULE_ONLY, or DISCARD
