"""Unit tests for SpecDesigner."""

from goldseam.core.spec_designer import SpecDesigner
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.llm.fake import FakeLLMClient
from goldseam.models.diagnosis import Diagnosis, EvidenceSpan, Route
from goldseam.models.spec import RiskLevel


def test_spec_designer_synthesis() -> None:
    adapter = TerminalLogAdapter()
    trace = adapter.ingest("Error: UnicodeDecodeError: unexpected byte 0x80")

    diag = Diagnosis(
        failure_class="DATA_PARSING_FAILURE",
        root_cause="Unicode byte decoding failure",
        capability_gap="Unicode normalizer tool",
        evidence_spans=[EvidenceSpan(event_index=0, snippet="UnicodeDecodeError")],
        confidence=0.95,
        recommended_route=Route.SKILL,
        rationale="Clear reusable capability",
    )

    designer = SpecDesigner(FakeLLMClient())
    spec = designer.design_spec(trace, diag)

    assert spec.slug == "unicode-normalizer"
    assert spec.risk_assessment is not None
    assert spec.risk_assessment.level == RiskLevel.LOW
    assert spec.replay_oracle is not None
    assert len(spec.replay_oracle.trace_hash) == 64
