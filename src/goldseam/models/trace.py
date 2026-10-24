"""Data models for failure traces and normalized event streams."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TraceEventKind(StrEnum):
    COMMAND = "command"
    STDOUT = "stdout"
    STDERR = "stderr"
    PROMPT = "prompt"
    RESPONSE = "response"
    DIFF = "diff"
    ENVIRONMENT = "environment"
    ERROR = "error"


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0, description="0-indexed position within the trace")
    kind: TraceEventKind = Field(description="Classification of event")
    text: str = Field(description="Event text content")
    exit_code: int | None = Field(
        default=None, description="Process exit code if command/execution"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Safe, sanitized metadata attributes"
    )


class NormalizedTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str = Field(
        min_length=1, max_length=256, description="Origin or ingest adapter identifier"
    )
    events: list[TraceEvent] = Field(
        min_length=1, description="Chronological sequence of trace events"
    )
    error_signature: str = Field(min_length=1, description="Normalized canonical error signature")
    redaction_counts: dict[str, int] = Field(
        default_factory=dict, description="Counts of redacted secret types"
    )
    injection_flags: list[str] = Field(
        default_factory=list, description="Detected prompt injection / override patterns"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Bounded safe context metadata"
    )

    @field_validator("events")
    @classmethod
    def validate_event_indices(cls, v: list[TraceEvent]) -> list[TraceEvent]:
        indices = [e.index for e in v]
        if len(indices) != len(set(indices)):
            raise ValueError("Trace events must have unique indices")
        return v
