"""Hardened Docker container sandbox runner."""

import subprocess
import time
from pathlib import Path

from goldseam.errors import SandboxBlockedError
from goldseam.models.result import SandboxResult
from goldseam.sandbox.base import SandboxRunner


class DockerSandboxRunner(SandboxRunner):
    name = "docker"
    is_hardened = True

    def __init__(self, image: str = "goldseam-sandbox:latest") -> None:
        self.image = image

    def is_available(self) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                return True, "Docker daemon running"
            return False, f"Docker command exited with code {res.returncode}: {res.stderr.strip()}"
        except FileNotFoundError:
            return False, "Docker CLI not found on system PATH"
        except subprocess.TimeoutExpired:
            return False, "Docker daemon connection timed out"
        except Exception as e:
            return False, f"Docker daemon check error: {e}"

    def run(
        self,
        staging_dir: Path,
        test_target: str = "tests",
        timeout_sec: int = 30,
        memory_limit: str = "512m",
    ) -> SandboxResult:
        avail, reason = self.is_available()
        if not avail:
            raise SandboxBlockedError(
                f"Hardened Docker sandbox is unavailable ({reason}). "
                "In accordance with Sandbox Fail-Closed policy, execution is blocked."
            )

        # Hardened container execution arguments
        # Explicit argument array - NO shell interpolation
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--user",
            "10001:10001",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--memory",
            memory_limit,
            "--cpus",
            "1.0",
            "--pids-limit",
            "64",
            "--volume",
            f"{staging_dir.resolve()}:/workspace:ro",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            self.image,
            "pytest",
            test_target,
            "-q",
        ]

        start_time = time.perf_counter()
        timed_out = False
        oom_killed = False

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            exit_code = res.returncode
            stdout = res.stdout[:50000]
            stderr = res.stderr[:50000]
            if exit_code == 137:
                oom_killed = True
        except subprocess.TimeoutExpired as e:
            timed_out = True
            exit_code = -1
            stdout = (e.stdout or "")[:50000] if isinstance(e.stdout, str) else ""
            stderr = (e.stderr or "")[:50000] if isinstance(e.stderr, str) else "Execution timed out"

        duration_ms = (time.perf_counter() - start_time) * 1000

        return SandboxResult(
            backend=self.name,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            oom_killed=oom_killed,
            isolated=True,
        )
