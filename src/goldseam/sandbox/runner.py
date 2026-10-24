"""Sandbox runner factory and backend selector."""

from goldseam.config import GoldseamConfig
from goldseam.sandbox.backends.docker import DockerSandboxRunner
from goldseam.sandbox.backends.local import LocalSubprocessRunner
from goldseam.sandbox.base import SandboxRunner


def get_sandbox_runner(
    preference: str = "auto",
    allow_weak: bool = False,
    config: GoldseamConfig | None = None,
) -> SandboxRunner:
    """
    Selects and instantiates the appropriate sandbox execution backend.
    Enforces fail-closed semantics when hardened isolation is unavailable.
    """
    cfg = config or GoldseamConfig.load()
    allow_weak_effective = allow_weak or cfg.allow_weak_sandbox

    if preference == "local":
        return LocalSubprocessRunner(allow_weak=allow_weak_effective)

    if preference == "docker":
        return DockerSandboxRunner(image=cfg.docker_image)

    # Preference: "auto"
    docker_runner = DockerSandboxRunner(image=cfg.docker_image)
    is_docker_avail, _ = docker_runner.is_available()

    if is_docker_avail:
        return docker_runner

    if allow_weak_effective:
        return LocalSubprocessRunner(allow_weak=True)

    # Fail-closed default: return docker runner which will fail closed on run()
    return docker_runner
