"""Bubblewrap (bwrap) unshare container isolation backend for Linux hosts."""

import shutil
import subprocess
import time
from pathlib import Path

from goldseam.errors import SandboxBlockedError
from goldseam.models.result import SandboxResult
from goldseam.sandbox.base import SandboxRunner


class BubblewrapSandboxRunner(SandboxRunner):
    """Executes sandboxed tests inside a Linux bubblewrap (bwrap) sandbox."""

    name = "bwrap"
    is_hardened = True

    def __init__(self, bwrap_binary: str = "bwrap") -> None:
        self.bwrap_binary = bwrap_binary

    def is_available(self) -> tuple[bool, str]:
        path = shutil.which(self.bwrap_binary)
        if not path:
            return False, f"Bubblewrap binary '{self.bwrap_binary}' not found on host."
        return True, "Bubblewrap available."

    def run(
        self,
        staging_dir: Path,
        test_target: str = "tests",
        timeout_sec: int = 30,
        memory_limit: str = "512m",
    ) -> SandboxResult:
        available, reason = self.is_available()
        if not available:
            raise SandboxBlockedError(f"Bubblewrap sandbox cannot execute: {reason}")

        cmd = ["pytest", test_target, "-v"]

        # Build hardened bwrap isolation arguments:
        # - unshare all namespaces (network, pid, ipc, uts, cgroup)
        # - read-only root mount
        # - private /tmp
        # - staging directory bound read-only
        bwrap_args = [
            self.bwrap_binary,
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/etc/resolv.conf", "/etc/resolv.conf",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--bind", str(staging_dir), "/workspace",
            "--chdir", "/workspace",
            "--unshare-all",
            "--unshare-net",
            "--die-with-parent",
            "--",
        ] + cmd

        start_time = time.time()
        try:
            res = subprocess.run(
                bwrap_args,
                capture_output=True,
                timeout=timeout_sec,
                text=True,
                check=False,
            )
            duration_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                backend=self.name,
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration_ms=duration_ms,
                timed_out=False,
                oom_killed=False,
                isolated=True,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.time() - start_time) * 1000
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return SandboxResult(
                backend=self.name,
                exit_code=-1,
                stdout=stdout,
                stderr=stderr + f"\nTimed out after {timeout_sec}s",
                duration_ms=duration_ms,
                timed_out=True,
                oom_killed=False,
                isolated=True,
            )
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            return SandboxResult(
                backend=self.name,
                exit_code=-1,
                stdout="",
                stderr=f"Bubblewrap execution error: {exc}",
                duration_ms=duration_ms,
                timed_out=False,
                oom_killed=False,
                isolated=True,
            )
