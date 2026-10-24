"""Weak local subprocess runner (strictly restricted to explicit opt-in for trusted development fixtures)."""

import os
import subprocess
import sys
import time
from pathlib import Path

from goldseam.errors import SandboxBlockedError
from goldseam.models.result import SandboxResult
from goldseam.sandbox.base import SandboxRunner


class LocalSubprocessRunner(SandboxRunner):
    name = "local"
    is_hardened = False

    def __init__(self, allow_weak: bool = False) -> None:
        self.allow_weak = allow_weak

    def is_available(self) -> tuple[bool, str]:
        if not self.allow_weak:
            return False, "Weak local sandbox requires explicit opt-in (--allow-weak-sandbox)"
        return True, "Weak local subprocess runner enabled (UNHARDENED)"

    def run(
        self,
        staging_dir: Path,
        test_target: str = "tests",
        timeout_sec: int = 30,
        memory_limit: str = "512m",
    ) -> SandboxResult:
        if not self.allow_weak:
            raise SandboxBlockedError(
                "Execution rejected: The local subprocess backend is unhardened and does not "
                "provide container isolation. Untrusted generated code must not run on host. "
                "Use --allow-weak-sandbox only for trusted offline unit test fixtures."
            )

        # Build clean scrubbed environment to prevent ambient secret leakage
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(staging_dir.resolve()),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }

        cmd = [sys.executable, "-m", "pytest", test_target, "-q"]

        start_time = time.perf_counter()
        timed_out = False

        try:
            res = subprocess.run(
                cmd,
                cwd=str(staging_dir.resolve()),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            exit_code = res.returncode
            stdout = res.stdout[:50000]
            stderr = res.stderr[:50000]
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
            oom_killed=False,
            isolated=False,  # Explicitly unhardened / non-isolated
        )
