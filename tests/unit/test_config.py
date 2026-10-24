"""Unit tests for configuration loader and precedence resolution."""

import os

from goldseam.config import GoldseamConfig


def test_config_defaults() -> None:
    config = GoldseamConfig.load()
    assert config.sandbox_backend == "auto"
    assert config.allow_weak_sandbox is False
    assert config.max_repair_iterations == 3
    assert config.budget_usd == 1.00


def test_config_env_overrides(monkeypatch: object) -> None:
    # Use monkeypatch safely or os.environ directly
    os.environ["GOLDSEAM_SANDBOX_BACKEND"] = "local"
    os.environ["GOLDSEAM_ALLOW_WEAK_SANDBOX"] = "true"
    os.environ["GOLDSEAM_MAX_REPAIR_ITERATIONS"] = "5"
    try:
        config = GoldseamConfig.load()
        assert config.sandbox_backend == "local"
        assert config.allow_weak_sandbox is True
        assert config.max_repair_iterations == 5
    finally:
        os.environ.pop("GOLDSEAM_SANDBOX_BACKEND", None)
        os.environ.pop("GOLDSEAM_ALLOW_WEAK_SANDBOX", None)
        os.environ.pop("GOLDSEAM_MAX_REPAIR_ITERATIONS", None)


def test_config_explicit_overrides() -> None:
    config = GoldseamConfig.load(overrides={"budget_usd": 2.50, "policy_preset": "permissive"})
    assert config.budget_usd == 2.50
    assert config.policy_preset == "permissive"
