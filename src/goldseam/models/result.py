"""Data models for sandbox execution outcomes, quality gates, and repair attempts."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GateOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    TIMEOUT = "TIMEOUT"
    OOM = "OOM"
    CRASH = "CRASH"
    POLICY = "POLICY"
    BLOCKED = "BLOCKED"


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: str = Field(min_length=1, description="Unique identifier of the verification gate")
    passed: bool = Field(description="True if gate criteria were satisfied")
    outcome: GateOutcome = Field(description="Structured categorical outcome")
    evidence: str = Field(
        default="", description="Diagnostic details, stdout/stderr, or policy violation trace"
    )
    duration_ms: float = Field(
        default=0.0, ge=0.0, description="Gate execution duration in milliseconds"
    )


class SandboxResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str = Field(description="Sandbox backend name (e.g. docker, local)")
    exit_code: int = Field(description="Process exit code")
    stdout: str = Field(default="", description="Sanitized stdout from sandbox")
    stderr: str = Field(default="", description="Sanitized stderr from sandbox")
    duration_ms: float = Field(ge=0.0, description="Wall-clock execution duration in milliseconds")
    timed_out: bool = Field(default=False, description="True if killed by timeout deadline")
    oom_killed: bool = Field(default=False, description="True if killed due to memory limit")
    isolated: bool = Field(
        default=True, description="True if executed under verified container isolation"
    )

    @property
    def outcome(self) -> GateOutcome:
        if self.timed_out:
            return GateOutcome.TIMEOUT
        if self.oom_killed:
            return GateOutcome.OOM
        if self.exit_code == 0:
            return GateOutcome.PASS
        return GateOutcome.FAIL


class Attempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_number: int = Field(
        ge=1, description="Iteration number in the compilation/repair cycle"
    )
    bundle_hash: str = Field(
        min_length=64, max_length=64, description="SHA-256 hash of the generated bundle"
    )
    gate_results: list[GateResult] = Field(
        description="Results of all evaluated verification gates"
    )
    token_usage: dict[str, int] = Field(
        default_factory=dict, description="Tokens consumed during this attempt"
    )
    cost_usd: float = Field(default=0.0, ge=0.0, description="Calculated monetary spend in USD")
    passed: bool = Field(description="True if all required gates passed")
