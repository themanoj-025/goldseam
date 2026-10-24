"""Unit tests for Phase 1 data contracts and models."""

import pytest
from pydantic import ValidationError

from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.diagnosis import Diagnosis, EvidenceSpan, Route
from goldseam.models.provenance import ProvenanceRecord
from goldseam.models.spec import (
    Example,
    SideEffect,
    SkillSpec,
    ToolSpec,
)
from goldseam.models.trace import NormalizedTrace, TraceEvent, TraceEventKind


def test_trace_models() -> None:
    event1 = TraceEvent(index=0, kind=TraceEventKind.COMMAND, text="npm test")
    event2 = TraceEvent(
        index=1, kind=TraceEventKind.STDERR, text="SyntaxError: Unexpected token", exit_code=1
    )

    trace = NormalizedTrace(
        source="pytest_log",
        events=[event1, event2],
        error_signature="SyntaxError: Unexpected token",
        redaction_counts={"API_KEY": 1},
    )
    assert trace.source == "pytest_log"
    assert len(trace.events) == 2

    # Reject duplicate event indices
    with pytest.raises(ValidationError):
        NormalizedTrace(
            source="test",
            events=[event1, TraceEvent(index=0, kind=TraceEventKind.STDOUT, text="dup")],
            error_signature="sig",
        )


def test_diagnosis_models() -> None:
    span = EvidenceSpan(event_index=1, line_start=5, line_end=6, snippet="SyntaxError")
    diag = Diagnosis(
        failure_class="SYNTAX_ERROR",
        root_cause="Unescaped unicode characters",
        capability_gap="JSON unicode normalization",
        evidence_spans=[span],
        confidence=0.95,
        recommended_route=Route.SKILL,
        rationale="Clear reusable parsing logic",
    )
    assert diag.confidence == 0.95
    assert diag.recommended_route == Route.SKILL


def test_spec_models_validation() -> None:
    ex1 = Example(inputs={"data": "abc"}, expected="ABC", should_fail=False)
    ex2 = Example(inputs={"data": "123"}, expected="123", should_fail=False)
    ex3 = Example(inputs={"data": ""}, expected="EMPTY", should_fail=True)  # negative example

    tool = ToolSpec(
        name="normalize_text",
        purpose="Normalizes text casing and whitespace.",
        input_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[ex1, ex2, ex3],
    )
    assert tool.name == "normalize_text"

    # Tool without negative example must fail validation
    with pytest.raises(ValidationError, match="must have at least one negative example"):
        ToolSpec(
            name="bad_tool",
            purpose="Tool with no negative examples",
            input_schema={},
            output_schema={},
            side_effects=[SideEffect.NONE],
            examples=[ex1, ex2, ex1],
        )

    # Invalid slug must fail validation (e.g. uppercase or consecutive hyphens)
    with pytest.raises(ValidationError, match="Slug"):
        SkillSpec(
            slug="Invalid--Slug",
            description="A test skill description.",
            triggers=["normalize"],
            non_triggers=["database"],
            tools=[tool],
        )

    # Valid SkillSpec
    skill = SkillSpec(
        slug="text-normalizer",
        description="Normalizes messy unicode text strings into canonical format.",
        triggers=["normalize unicode", "clean text"],
        non_triggers=["database migration"],
        tools=[tool],
    )
    assert skill.slug == "text-normalizer"


def test_bundle_models_safety() -> None:
    # Reject path traversal
    with pytest.raises(ValidationError, match="Path traversal"):
        GeneratedFile(path="../evil.py", content="print(1)")

    # Reject absolute path
    with pytest.raises(ValidationError, match="relative path"):
        GeneratedFile(path="/etc/passwd", content="root:x:0:0")

    # Reject Windows reserved device name
    with pytest.raises(ValidationError, match="reserved device name"):
        GeneratedFile(path="scripts/NUL.py", content="print(1)")

    # Valid bundle requires SKILL.md
    f_code = GeneratedFile(path="scripts/main.py", content="def main(): pass")
    with pytest.raises(ValidationError, match="missing required root 'SKILL.md'"):
        GeneratedBundle(skill_slug="text-tool", files=[f_code])

    f_skill = GeneratedFile(path="SKILL.md", content="# Skill")
    bundle = GeneratedBundle(skill_slug="text-tool", files=[f_code, f_skill])
    assert bundle.get_file("scripts/main.py") == f_code


def test_provenance_verification() -> None:
    files = {
        "SKILL.md": "# Text Tool",
        "scripts/tool.py": "def run(): return 42",
    }
    artifact_hashes = {
        path: ProvenanceRecord.compute_sha256(content) for path, content in files.items()
    }

    record = ProvenanceRecord(
        timestamp="2026-10-24T12:00:00Z",
        skill_slug="text-tool",
        redacted_trace_hash="a" * 64,
        model_ids={"generator": "fake-v1"},
        prompt_versions={"spec": "v1.0"},
        policy_hash="b" * 64,
        gate_results=[],
        artifact_hashes=artifact_hashes,
    )

    valid, discrepancies = record.verify_artifacts(files)
    assert valid
    assert len(discrepancies) == 0

    # Modify single byte in scripts/tool.py
    tampered_files = dict(files)
    tampered_files["scripts/tool.py"] = "def run(): return 43"
    valid, discrepancies = record.verify_artifacts(tampered_files)
    assert not valid
    assert any("Integrity mismatch" in d for d in discrepancies)
