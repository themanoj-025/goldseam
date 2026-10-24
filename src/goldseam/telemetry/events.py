"""Telemetry events emitted across compilation state machine transitions."""

import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    event_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    event_type: str
    run_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class StageTransitionEvent(TelemetryEvent):
    event_type: str = "stage_transition"
    from_stage: str
    to_stage: str


class GateCompletedEvent(TelemetryEvent):
    event_type: str = "gate_completed"
    gate_name: str
    passed: bool
    outcome: str
    duration_ms: float = 0.0


class RepairIterationEvent(TelemetryEvent):
    event_type: str = "repair_iteration"
    attempt_number: int
    patch_summary: str
