"""Abstract base class for execution sandbox backends."""

from abc import ABC, abstractmethod
from pathlib import Path

from goldseam.models.result import SandboxResult


class SandboxRunner(ABC):
    name: str
    is_hardened: bool

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Returns (is_available, status_or_reason)."""

    @abstractmethod
    def run(
        self,
        staging_dir: Path,
        test_target: str = "tests",
        timeout_sec: int = 30,
        memory_limit: str = "512m",
    ) -> SandboxResult:
        """Executes test suite in sandbox staging environment."""
