from typing import Any, TypeVar, cast

from pydantic import BaseModel

from goldseam.errors import LLMProviderError
from goldseam.llm.base import LLMClient, LLMResponse
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.diagnosis import Diagnosis, EvidenceSpan, Route
from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec

T = TypeVar("T", bound=BaseModel)


class FakeLLMClient(LLMClient):
    name = "fake"

    def __init__(self, seeded_responses: dict[type, Any] | None = None) -> None:
        self.seeded_responses = seeded_responses or {}
        self.call_history: list[tuple[str, type]] = []

    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        self.call_history.append((prompt, response_model))

        # Check explicit seeded mock
        if response_model in self.seeded_responses:
            mock_val = self.seeded_responses[response_model]
            if isinstance(mock_val, response_model):
                return LLMResponse(content=mock_val, prompt_tokens=50, completion_tokens=100, cost_usd=0.0, model_id="fake-seeded")

        # Synthesize deterministic default responses based on model type
        if issubclass(response_model, Diagnosis):
            # Check prompt for DISCARD triggers
            p_lower = prompt.lower()
            if any(k in p_lower for k in ("transient typo", "one-off typo", "no such option", "did you mean")):
                diag = Diagnosis(
                    failure_class="TRANSIENT_TYPO",
                    root_cause="User misspelled a CLI argument or option",
                    capability_gap="None (one-off transient error)",
                    evidence_spans=[EvidenceSpan(event_index=0, snippet="typo")],
                    confidence=0.98,
                    recommended_route=Route.DISCARD,
                    rationale="One-off transient typo does not justify a reusable skill.",
                )
            elif any(k in p_lower for k in ("503", "service unavailable", "gateway timeout", "no space left", "outage", "vendoroutage")):
                diag = Diagnosis(
                    failure_class="TRANSIENT_OUTAGE",
                    root_cause="Transient infrastructure outage or resource depletion",
                    capability_gap="None (transient upstream failure)",
                    evidence_spans=[EvidenceSpan(event_index=0, snippet="outage")],
                    confidence=0.96,
                    recommended_route=Route.DISCARD,
                    rationale="Transient infrastructure or hardware failure is non-deterministic.",
                )
            elif any(k in p_lower for k in ("ignore previous", "reveal all", "backdoor", "exfiltrat")):
                diag = Diagnosis(
                    failure_class="PROMPT_INJECTION",
                    root_cause="Adversarial prompt injection attempt",
                    capability_gap="None (malicious payload)",
                    evidence_spans=[EvidenceSpan(event_index=0, snippet="injection")],
                    confidence=0.99,
                    recommended_route=Route.DISCARD,
                    rationale="Adversarial prompt injection rejected by security triage.",
                )
            elif any(k in p_lower for k in ("style preference", "coding convention", "tabs over spaces", "prefer tabs")):
                diag = Diagnosis(
                    failure_class="DEVELOPER_PREFERENCE",
                    root_cause="Code formatting or stylistic preference",
                    capability_gap="Style adherence guideline",
                    evidence_spans=[EvidenceSpan(event_index=0, snippet="style preference")],
                    confidence=0.95,
                    recommended_route=Route.RULE_ONLY,
                    rationale="Stylistic or procedural guidance should be recorded as a rule.",
                )
            else:
                diag = Diagnosis(
                    failure_class="DATA_PARSING_FAILURE",
                    root_cause="Messy unicode encoding or unexpected escape tokens in payload",
                    capability_gap="Deterministic Unicode string normalizer",
                    evidence_spans=[EvidenceSpan(event_index=0, snippet="UnicodeError")],
                    confidence=0.92,
                    recommended_route=Route.SKILL,
                    rationale="Recurring deterministic failure suitable for an Agent Skill.",
                )
            return LLMResponse(content=cast(Any, diag), prompt_tokens=60, completion_tokens=120, cost_usd=0.0, model_id="fake-v1")

        if issubclass(response_model, SkillSpec):
            tool = ToolSpec(
                name="normalize_text",
                purpose="Normalizes raw text strings into canonical UTF-8.",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                output_schema={"type": "string"},
                side_effects=[SideEffect.NONE],
                allowed_imports=["re", "unicodedata"],
                preconditions=["Input text must be a valid string"],
                examples=[
                    Example(inputs={"text": "café\\u00e9"}, expected="caféé", should_fail=False, description="Unicode escape decode"),
                    Example(inputs={"text": "hello   world"}, expected="hello world", should_fail=False, description="Whitespace collapse"),
                    Example(inputs={"text": None}, expected="Error: invalid text", should_fail=True, description="None input rejection"),
                ],
            )
            spec = SkillSpec(
                slug="unicode-normalizer",
                description="Normalizes raw text containing messy unicode escapes into clean UTF-8. Use when handling dirty text streams.",
                triggers=["normalize unicode", "clean text escapes"],
                non_triggers=["database migration", "network requests"],
                tools=[tool],
            )
            return LLMResponse(content=cast(Any, spec), prompt_tokens=120, completion_tokens=250, cost_usd=0.0, model_id="fake-v1")

        if issubclass(response_model, GeneratedBundle):
            skill_md = """---
name: unicode-normalizer
description: Normalizes raw text containing messy unicode escapes into clean UTF-8.
license: Apache-2.0
compatibility: Python >=3.11
---

# Unicode Normalizer

## When to Use
- Normalizing dirty text with unicode escapes

## When Not to Use
- Database migration

## Preconditions
- Input is text string

## Steps
1. Execute `scripts/normalizer.py`

## Examples
- `normalize_text({"text": "abc"})`

## Failure Modes
- Non-string inputs exit with code 1

## Safety Notes
- Pure computation
"""
            code_py = """import unicodedata
import sys
import json

def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Input must be string")
    return unicodedata.normalize('NFKC', text).strip()

if __name__ == '__main__':
    raw = sys.stdin.read()
    data = json.loads(raw)
    out = normalize_text(data["text"])
    print(json.dumps({"result": out}))
"""
            test_py = """import pytest
from scripts.normalizer import normalize_text

def test_normalize_valid():
    assert normalize_text("hello  ") == "hello"

def test_normalize_invalid():
    with pytest.raises(ValueError):
        normalize_text(123)  # type: ignore
"""
            bundle = GeneratedBundle(
                skill_slug="unicode-normalizer",
                files=[
                    GeneratedFile(path="SKILL.md", content=skill_md),
                    GeneratedFile(path="scripts/normalizer.py", content=code_py, is_executable=True),
                    GeneratedFile(path="tests/test_normalizer.py", content=test_py),
                ],
            )
            return LLMResponse(content=cast(Any, bundle), prompt_tokens=200, completion_tokens=400, cost_usd=0.0, model_id="fake-v1")

        raise LLMProviderError(f"FakeLLMClient has no default factory for response model '{response_model.__name__}'")
