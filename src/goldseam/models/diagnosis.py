"""Data models for triage, diagnosis, and capability routing."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Route(StrEnum):
    SKILL = "SKILL"
    SCRIPT = "SCRIPT"
    MCP_TOOL = "MCP_TOOL"
    RULE_ONLY = "RULE_ONLY"
    DISCARD = "DISCARD"


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_index: int = Field(ge=0, description="Index of the trace event")
    line_start: int | None = Field(default=None, ge=1, description="Start line within event text")
    line_end: int | None = Field(default=None, ge=1, description="End line within event text")
    snippet: str = Field(min_length=1, description="Excerpt of evidence text")


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    failure_class: str = Field(
        min_length=1, max_length=128, description="Taxonomic class of failure"
    )
    root_cause: str = Field(min_length=1, description="Technical root cause analysis")
    capability_gap: str = Field(
        min_length=1, description="Precise description of the missing capability"
    )
    evidence_spans: list[EvidenceSpan] = Field(
        min_length=1, description="Verifiable citations from the trace"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Diagnostic confidence score in [0.0, 1.0]"
    )
    recommended_route: Route = Field(description="Initial route recommendation from triage")
    rationale: str = Field(min_length=1, description="Human-readable justification for route")
