"""Unit tests for TriageEngine and CapabilityRouter."""

from goldseam.core.router import CapabilityRouter
from goldseam.core.triage import TriageEngine
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.llm.fake import FakeLLMClient
from goldseam.models.diagnosis import Diagnosis, EvidenceSpan, Route


def test_triage_engine_and_router_flow() -> None:
    adapter = TerminalLogAdapter()
    trace = adapter.ingest("Error: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff")

    llm = FakeLLMClient()
    engine = TriageEngine(llm)
    diagnosis = engine.triage(trace)

    assert diagnosis.confidence >= 0.90
    assert diagnosis.recommended_route == Route.SKILL

    router = CapabilityRouter()
    route, rationale = router.route(diagnosis)
    assert route == Route.SKILL


def test_router_discards_transient_and_low_confidence() -> None:
    router = CapabilityRouter()

    low_conf_diag = Diagnosis(
        failure_class="UNKNOWN",
        root_cause="Vague error",
        capability_gap="Unclear",
        evidence_spans=[EvidenceSpan(event_index=0, snippet="err")],
        confidence=0.30,  # Below 0.50 threshold
        recommended_route=Route.SKILL,
        rationale="Uncertain",
    )
    route, rationale = router.route(low_conf_diag)
    assert route == Route.DISCARD
    assert "below threshold" in rationale
