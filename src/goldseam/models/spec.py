"""Data models for ToolSpec, SkillSpec, and trusted RiskAssessment."""

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SideEffect(StrEnum):
    NONE = "NONE"
    READ_WORKSPACE = "READ_WORKSPACE"
    WRITE_WORKSPACE = "WRITE_WORKSPACE"
    NETWORK = "NETWORK"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    level: RiskLevel = Field(description="Deterministic trusted risk level")
    justification: str = Field(min_length=1, description="Rule-based risk justification")
    evaluated_by: str = Field(min_length=1, description="Policy evaluator identifier")
    declared_side_effects: list[SideEffect] = Field(default_factory=list)
    flagged_imports: list[str] = Field(default_factory=list)


class Example(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: dict[str, Any] = Field(description="Dictionary of input parameters")
    expected: Any = Field(description="Expected output value or structure")
    should_fail: bool = Field(
        default=False, description="True if this is a negative/error-handling example"
    )
    description: str = Field(default="", description="Description of the test scenario")


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=64, description="Valid Python function identifier")
    purpose: str = Field(
        min_length=10, max_length=1024, description="Clear statement of function purpose"
    )
    input_schema: dict[str, Any] = Field(description="JSON Schema for function inputs")
    output_schema: dict[str, Any] = Field(description="JSON Schema for function return value")
    side_effects: list[SideEffect] = Field(
        min_length=1, description="Explicitly declared side-effects"
    )
    allowed_imports: list[str] = Field(
        default_factory=list, description="Whitelisted modules required"
    )
    preconditions: list[str] = Field(
        default_factory=list, description="Preconditions required before execution"
    )
    examples: list[Example] = Field(
        min_length=3, description="At least 3 examples with >=1 negative case"
    )

    @field_validator("name")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Tool name '{v}' must be a valid Python identifier")
        return v

    @model_validator(mode="after")
    def validate_negative_example_exists(self) -> "ToolSpec":
        if not any(ex.should_fail for ex in self.examples):
            raise ValueError(
                f"Tool '{self.name}' must have at least one negative example (should_fail=True)"
            )
        return self


class ReplayOracle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trace_hash: str = Field(
        min_length=64, max_length=64, description="SHA-256 of the redacted source trace"
    )
    sanitized_input: dict[str, Any] = Field(
        description="Sanitized input reproducing the original failure condition"
    )
    expected_outcome: Any = Field(description="Expected deterministic output or error behavior")
    oracle_hash: str = Field(
        min_length=64, max_length=64, description="SHA-256 hash of this oracle record"
    )


class SkillSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slug: str = Field(
        min_length=1, max_length=64, description="Hyphenated slug for skill directory and package"
    )
    description: str = Field(
        min_length=10, max_length=1024, description="Official Agent Skills description"
    )
    triggers: list[str] = Field(
        min_length=1, description="Keywords and intent descriptions when this skill applies"
    )
    non_triggers: list[str] = Field(
        min_length=1, description="Scenarios where this skill MUST NOT be invoked"
    )
    non_goals: list[str] = Field(
        default_factory=list, description="Explicit out-of-scope boundaries"
    )
    tools: list[ToolSpec] = Field(
        min_length=1, description="Typed tools packaged within this skill"
    )
    replay_oracle: ReplayOracle | None = Field(
        default=None, description="Cryptographically locked replay anchor"
    )
    risk_assessment: RiskAssessment | None = Field(
        default=None, description="Trusted computed risk assessment"
    )
    compatibility: str = Field(
        default="Python >=3.11", max_length=500, description="Runtime compatibility requirement"
    )
    license: str = Field(default="Apache-2.0", description="License identifier")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        # Agent Skills specification: max 64 chars, lowercase alphanumeric and hyphens, no consecutive hyphens
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError(
                f"Slug '{v}' must be lowercase alphanumeric with single hyphens, e.g. 'json-normalizer'"
            )
        return v
