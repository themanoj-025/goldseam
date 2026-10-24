"""Tests for DockerSandboxRunner and fail-closed isolation contracts."""

from pathlib import Path

import pytest

from goldseam.errors import SandboxBlockedError
from goldseam.sandbox.backends.docker import DockerSandboxRunner
from goldseam.sandbox.runner import get_sandbox_runner


def test_docker_runner_fail_closed_when_daemon_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = DockerSandboxRunner()

    # Simulate daemon offline
    monkeypatch.setattr(runner, "is_available", lambda: (False, "Daemon offline simulated"))

    with pytest.raises(SandboxBlockedError, match="Fail-Closed"):
        runner.run(Path("/tmp/stage"))


def test_get_sandbox_runner_auto_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    # When docker is available, selects docker runner
    monkeypatch.setattr(
        DockerSandboxRunner, "is_available", lambda self: (True, "Running")
    )
    runner = get_sandbox_runner(preference="auto", allow_weak=False)
    assert runner.name == "docker"
    assert runner.is_hardened is True

    # When docker is unavailable and weak not allowed, returns docker (which fails closed)
    monkeypatch.setattr(
        DockerSandboxRunner, "is_available", lambda self: (False, "Offline")
    )
    runner_blocked = get_sandbox_runner(preference="auto", allow_weak=False)
    assert runner_blocked.name == "docker"

    # When docker is unavailable and weak is allowed, returns local
    runner_local = get_sandbox_runner(preference="auto", allow_weak=True)
    assert runner_local.name == "local"
    assert runner_local.is_hardened is False
