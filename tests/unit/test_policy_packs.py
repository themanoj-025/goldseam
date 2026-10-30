"""Unit tests for security policy packs and reproducible build metadata."""

from goldseam.security.policy_packs import PolicyPackManager


def test_compute_reproducible_metadata() -> None:
    meta = PolicyPackManager.compute_reproducible_metadata()
    assert "goldseam_version" in meta
    assert "python_version" in meta
    assert "platform_system" in meta
    assert "build_env_hash" in meta
    assert len(meta["build_env_hash"]) == 64


def test_strict_policy_pack() -> None:
    pack = PolicyPackManager.get_policy_pack("strict")
    assert pack.name == "strict"
    assert pack.network_allowed is False
    assert "re" in pack.allowed_imports
    assert "eval" in pack.disallowed_calls
    assert len(pack.reproducible_metadata) > 0


def test_data_science_policy_pack() -> None:
    pack = PolicyPackManager.get_policy_pack("data_science")
    assert pack.name == "data_science"
    assert "numpy" in pack.allowed_imports
    assert "statistics" in pack.allowed_imports


def test_unknown_preset_fails_closed_to_strict() -> None:
    pack = PolicyPackManager.get_policy_pack("nonexistent_preset")
    assert pack.name == "strict"
