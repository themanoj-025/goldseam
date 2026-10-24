"""Trace analyzer extracting failure signatures, recurrence patterns, and error clustering."""

from pydantic import BaseModel, Field

from goldseam.models.trace import NormalizedTrace, TraceEventKind


class TraceAnalysis(BaseModel):
    total_events: int
    error_count: int
    command_count: int
    primary_signature: str
    recurrence_key: str
    has_stack_trace: bool
    detected_technologies: list[str] = Field(default_factory=list)


class TraceAnalyzer:
    """Analyzes normalized execution traces to extract structural telemetry and clustering keys."""

    def analyze(self, trace: NormalizedTrace) -> TraceAnalysis:
        error_events = [e for e in trace.events if e.kind == TraceEventKind.STDERR]
        cmd_events = [e for e in trace.events if e.kind == TraceEventKind.COMMAND]

        has_traceback = any("traceback" in e.text.lower() or "line " in e.text.lower() for e in trace.events)

        # Detect technologies mentioned in trace
        techs: list[str] = []
        all_text = " ".join(e.text for e in trace.events).lower()
        for tech in ("python", "docker", "git", "json", "csv", "regex", "pytest", "node", "curl"):
            if tech in all_text:
                techs.append(tech)

        # Recurrence key based on normalized error signature
        recurrence_key = trace.error_signature.split()[0] if trace.error_signature else "unknown_error"

        return TraceAnalysis(
            total_events=len(trace.events),
            error_count=len(error_events),
            command_count=len(cmd_events),
            primary_signature=trace.error_signature,
            recurrence_key=recurrence_key,
            has_stack_trace=has_traceback,
            detected_technologies=sorted(set(techs)),
        )
