"""Security tests for advanced sandbox backends: bwrap, wasm, and remote."""

from pathlib import Path

import pytest

from goldseam.errors import SandboxBlockedError
from goldseam.sandbox.backends.bwrap import BubblewrapSandboxRunner
from goldseam.sandbox.backends.remote import RemoteSandboxRunner
from goldseam.sandbox.backends.wasm import WasmSandboxRunner


def test_bwrap_fail_closed_when_missing(tmp_path: Path) -> None:
    runner = BubblewrapSandboxRunner(bwrap_binary="nonexistent_bwrap_bin")
    ok, msg = runner.is_available()
    assert ok is False
    assert "not found" in msg

    with pytest.raises(SandboxBlockedError, match="Bubblewrap sandbox cannot execute"):
        runner.run(tmp_path)


def test_wasm_fail_closed_when_missing(tmp_path: Path) -> None:
    runner = WasmSandboxRunner(runtime_bin="nonexistent_wasm_runtime")
    ok, msg = runner.is_available()
    assert ok is False
    assert "not found" in msg

    with pytest.raises(SandboxBlockedError, match="WASM sandbox cannot execute"):
        runner.run(tmp_path)


def test_remote_sandbox_fail_closed_missing_credentials(tmp_path: Path) -> None:
    # No credentials
    runner = RemoteSandboxRunner()
    ok, msg = runner.is_available()
    assert ok is False
    assert "credentials" in msg.lower()

    with pytest.raises(SandboxBlockedError, match="Remote sandbox execution rejected"):
        runner.run(tmp_path)


def test_remote_sandbox_fail_closed_missing_cost_approval(tmp_path: Path) -> None:
    # Credentials provided, but cost approval missing
    runner = RemoteSandboxRunner(
        endpoint_url="https://sandbox.internal/run",
        api_key="secret-token-12345",
        cost_approved=False,
        privacy_disclosed=True,
    )
    ok, msg = runner.is_available()
    assert ok is False
    assert "cost approval" in msg.lower()

    with pytest.raises(SandboxBlockedError, match="Explicit cost approval required"):
        runner.run(tmp_path)


def test_remote_sandbox_fail_closed_missing_privacy_disclosure(tmp_path: Path) -> None:
    # Credentials and cost approved, but privacy disclosure missing
    runner = RemoteSandboxRunner(
        endpoint_url="https://sandbox.internal/run",
        api_key="secret-token-12345",
        cost_approved=True,
        privacy_disclosed=False,
    )
    ok, msg = runner.is_available()
    assert ok is False
    assert "privacy disclosure" in msg.lower()

    with pytest.raises(SandboxBlockedError, match="Explicit user privacy disclosure required"):
        runner.run(tmp_path)


def test_remote_sandbox_success_when_authorized(tmp_path: Path) -> None:
    runner = RemoteSandboxRunner(
        endpoint_url="https://sandbox.internal/run",
        api_key="secret-token-12345",
        cost_approved=True,
        privacy_disclosed=True,
    )
    ok, _ = runner.is_available()
    assert ok is True

    res = runner.run(tmp_path)
    assert res.exit_code == 0
    assert res.isolated is True
