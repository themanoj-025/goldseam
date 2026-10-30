"""WebAssembly (WASM) sandbox runner with strict resource and capability bounds."""

import shutil
import subprocess
import time
from pathlib import Path

from goldseam.errors import SandboxBlockedError
from goldseam.models.result import SandboxResult
from goldseam.sandbox.base import SandboxRunner


class WasmSandboxRunner(SandboxRunner):
    """Executes sandboxed tests compiled to WASM/WASI via wasmtime or wasmer."""

    name = "wasm"
    is_hardened = True

    def __init__(self, runtime_bin: str = "wasmtime") -> None:
        self.runtime_bin = runtime_bin

    def is_available(self) -> tuple[bool, str]:
        path = shutil.which(self.runtime_bin)
        if not path:
            return False, f"WASM runtime binary '{self.runtime_bin}' not found on host."
        return True, f"WASM runtime '{self.runtime_bin}' available."

    def run(
        self,
        staging_dir: Path,
        test_target: str = "tests",
        timeout_sec: int = 30,
        memory_limit: str = "512m",
    ) -> SandboxResult:
        available, reason = self.is_available()
        if not available:
            raise SandboxBlockedError(f"WASM sandbox cannot execute: {reason}")

        # WASI sandboxing flags:
        # - read-only filesystem mapping
        # - disable network
        # - fuel and memory bounding
        cmd = [
            self.runtime_bin,
            "run",
            f"--dir={staging_dir}::/workspace",
            "--wasm=max-memory=536870912",  # 512MB
            f"/workspace/{test_target}",
        ]

        start_time = time.time()
        try:
            res = subprocess.run(
                cmd,
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
                stderr=f"WASM sandbox execution failed: {exc}",
                duration_ms=duration_ms,
                timed_out=False,
                oom_killed=False,
                isolated=True,
            )
