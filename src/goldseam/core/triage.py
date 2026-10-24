"""Triage engine diagnosing failures and synthesizing structured capability gap assessments."""

from goldseam.errors import TriageError
from goldseam.llm.base import LLMClient
from goldseam.models.diagnosis import Diagnosis
from goldseam.models.trace import NormalizedTrace

TRIAGE_PROMPT_TEMPLATE = """You are an expert diagnostic compiler.
Analyze the following normalized agent execution trace to diagnose whether a reusable capability gap exists.

Trace Source: {source}
Canonical Error Signature: {signature}

Trace Events:
{events_summary}

Determine:
1. Taxonomic failure class
2. Technical root cause
3. Missing capability gap
4. Verifiable evidence citations with event indices
5. Diagnostic confidence score [0.0 - 1.0]
6. Recommended route: SKILL, SCRIPT, MCP_TOOL, RULE_ONLY, or DISCARD.
"""


class TriageEngine:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def triage(self, trace: NormalizedTrace) -> Diagnosis:
        """Diagnoses failure trace and returns validated Diagnosis."""
        event_lines: list[str] = []
        for e in trace.events[:40]:  # Bound input event count
            event_lines.append(f"[{e.index}] ({e.kind.value}) {e.text[:200]}")
        events_summary = "\n".join(event_lines)

        prompt = TRIAGE_PROMPT_TEMPLATE.format(
            source=trace.source,
            signature=trace.error_signature,
            events_summary=events_summary,
        )

        response = self.llm_client.complete_structured(prompt, Diagnosis)
        diag = response.content

        # Validate evidence spans against real trace events to prevent hallucinations
        valid_indices = {e.index for e in trace.events}
        for span in diag.evidence_spans:
            if span.event_index not in valid_indices:
                raise TriageError(
                    f"Model hallucinated invalid event index {span.event_index}; trace only contains indices {sorted(valid_indices)[:10]}..."
                )

        return diag
