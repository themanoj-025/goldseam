"""Tests for AST analysis and policy enforcement."""

import pytest

from goldseam.security.ast_visitor import analyze_python_code
from goldseam.security.import_policy import SecurityPolicy


@pytest.fixture
def policy() -> SecurityPolicy:
    return SecurityPolicy.load_default()


def test_allowed_code(policy: SecurityPolicy) -> None:
    code = """
import json
import re
from datetime import datetime
from typing import Any

def clean_data(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r'\\s+', ' ', raw).strip()
    return {"timestamp": datetime.now().isoformat(), "value": json.loads(cleaned)}
"""
    findings, modules = analyze_python_code(code, policy, preset="strict")
    assert len(findings) == 0
    assert "json" in modules
    assert "re" in modules


def test_forbidden_eval_call(policy: SecurityPolicy) -> None:
    code = "result = eval('1 + 2')"
    findings, _ = analyze_python_code(code, policy, preset="strict")
    assert len(findings) > 0
    assert any(f.rule == "FORBIDDEN_CALL" and "eval" in f.message for f in findings)


def test_dunder_traversal_detection(policy: SecurityPolicy) -> None:
    code = "subclasses = ().__class__.__bases__[0].__subclasses__()"
    findings, _ = analyze_python_code(code, policy, preset="strict")
    assert len(findings) >= 2
    rules = [f.rule for f in findings]
    assert "FORBIDDEN_ATTRIBUTE" in rules
