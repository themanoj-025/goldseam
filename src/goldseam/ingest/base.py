"""Abstract base class for trace ingest adapters."""

from abc import ABC, abstractmethod
from pathlib import Path

from goldseam.models.trace import NormalizedTrace


class IngestAdapter(ABC):
    name: str

    @abstractmethod
    def ingest(self, raw_input: str | Path) -> NormalizedTrace:
        """Parses and normalizes raw input into a canonical NormalizedTrace."""
