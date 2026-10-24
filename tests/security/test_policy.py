"""Tests for SecurityPolicy and deterministic risk assessment."""

import pytest

from goldseam.models.spec import RiskLevel, SideEffect
from goldseam.security.import_policy import SecurityPolicy


@pytest.fixture
def policy() -> SecurityPolicy:
    return SecurityPolicy.load_default()


def test_pure_computation_is_low_risk(policy: SecurityPolicy) -> None:
    assessment = policy.evaluate_risk(
        declared_side_effects=[SideEffect.NONE],
        imported_modules=["json", "re", "math"],
        preset="strict",
    )
    assert assessment.level == RiskLevel.LOW
    assert "Pure deterministic computation" in assessment.justification


def test_network_side_effect_is_critical_risk(policy: SecurityPolicy) -> None:
    assessment = policy.evaluate_risk(
        declared_side_effects=[SideEffect.NETWORK],
        imported_modules=["json"],
        preset="strict",
    )
    assert assessment.level == RiskLevel.CRITICAL
    assert "Network access" in assessment.justification


def test_forbidden_module_is_critical_risk(policy: SecurityPolicy) -> None:
    assessment = policy.evaluate_risk(
        declared_side_effects=[SideEffect.NONE],
        imported_modules=["subprocess"],
        preset="strict",
    )
    assert assessment.level == RiskLevel.CRITICAL
    assert "Strictly forbidden" in assessment.justification


def test_write_workspace_is_high_risk(policy: SecurityPolicy) -> None:
    assessment = policy.evaluate_risk(
        declared_side_effects=[SideEffect.WRITE_WORKSPACE],
        imported_modules=["json", "pathlib"],
        preset="strict",
    )
    assert assessment.level == RiskLevel.HIGH


def test_read_workspace_is_medium_risk(policy: SecurityPolicy) -> None:
    assessment = policy.evaluate_risk(
        declared_side_effects=[SideEffect.READ_WORKSPACE],
        imported_modules=["json", "pathlib"],
        preset="strict",
    )
    assert assessment.level == RiskLevel.MEDIUM
