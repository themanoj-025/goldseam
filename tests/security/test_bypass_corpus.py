"""Adversarial bypass evaluation running 100+ attack snippets against AST visitor."""

import json
from pathlib import Path

import pytest

from goldseam.security.ast_visitor import analyze_python_code
from goldseam.security.import_policy import SecurityPolicy


@pytest.fixture
def corpus() -> list[dict[str, str]]:
    corpus_file = Path(__file__).parent / "bypass_corpus" / "snippets.json"
    with open(corpus_file, encoding="utf-8") as f:
        data = json.load(f)
    return data  # type: ignore[no-any-return]


def test_adversarial_bypass_corpus(corpus: list[dict[str, str]]) -> None:
    policy = SecurityPolicy.load_default()
    assert len(corpus) >= 100, f"Corpus must contain >= 100 snippets, got {len(corpus)}"

    unblocked: list[str] = []

    for item in corpus:
        snippet_id = item["id"]
        code = item["code"]
        findings, _ = analyze_python_code(code, policy, preset="strict")

        if len(findings) == 0:
            unblocked.append(f"{snippet_id}: {code}")

    assert len(unblocked) == 0, f"Unblocked adversarial snippets detected: {unblocked}"
