"""Opt-in live provider tests.

These hit real provider APIs and cost money, so they are never part of the
offline suite: each test skips unless its API key is configured.

Run against live providers:

    OPENAI_API_KEY=... uv run pytest tests/integration/test_live_providers.py -v

The nightly workflow (`.github/workflows/nightly-live.yml`) runs exactly this
file with a hard spend cap when `OPENAI_API_KEY` is present.
"""

from __future__ import annotations

import os

import pytest
from pydantic import BaseModel

from goldseam.llm.openai_provider import OpenAIClient


class Greeting(BaseModel):
    """Minimal structured-output model used to exercise the live adapter."""

    message: str


@pytest.fixture
def require_openai_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not configured")


def test_openai_structured_completion(require_openai_key: None) -> None:
    client = OpenAIClient()

    response = client.complete_structured(
        "Reply with a single short greeting.",
        Greeting,
    )

    assert response.content.message.strip()
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.cost_usd > 0.0
