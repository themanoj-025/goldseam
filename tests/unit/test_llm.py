"""Unit tests for FakeLLM client and budget tracking."""

import pytest

from goldseam.errors import BudgetExceededError
from goldseam.llm.budget import BudgetTracker
from goldseam.llm.fake import FakeLLMClient
from goldseam.models.diagnosis import Diagnosis
from goldseam.models.spec import SkillSpec


def test_fake_llm_client_synthesis() -> None:
    client = FakeLLMClient()
    resp_diag = client.complete_structured("trace with UnicodeError", Diagnosis)
    assert isinstance(resp_diag.content, Diagnosis)
    assert resp_diag.prompt_tokens > 0

    resp_spec = client.complete_structured("spec for normalizer", SkillSpec)
    assert isinstance(resp_spec.content, SkillSpec)
    assert resp_spec.content.slug == "unicode-normalizer"


def test_budget_tracker_enforcement() -> None:
    tracker = BudgetTracker(max_budget_usd=0.05, max_tokens=1000)

    # First small usage succeeds
    tracker.record_usage(prompt_tokens=200, completion_tokens=100, cost_usd=0.01)
    assert tracker.total_tokens == 300

    # Over budget raises BudgetExceededError
    with pytest.raises(BudgetExceededError, match="exceeded configured maximum budget"):
        tracker.record_usage(prompt_tokens=100, completion_tokens=100, cost_usd=0.05)
