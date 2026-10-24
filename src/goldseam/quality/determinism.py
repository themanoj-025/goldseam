"""Determinism evaluator verifying repeatable, bit-for-bit stable tool execution."""

import json
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class DeterminismResult(BaseModel):
    is_deterministic: bool
    iterations: int
    variance_detected: bool
    output_samples: list[str]


class DeterminismEvaluator:
    """Evaluates whether tool output is bit-for-bit identical across multiple invocations."""

    def __init__(self, sample_iterations: int = 5) -> None:
        self.sample_iterations = sample_iterations

    def evaluate_callable(
        self,
        func: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any] | None = None,
    ) -> DeterminismResult:
        kwargs = kwargs or {}
        samples: list[str] = []

        for _ in range(self.sample_iterations):
            out = func(*args, **kwargs)
            try:
                serialized = json.dumps(out, sort_keys=True)
            except Exception:
                serialized = str(out)
            samples.append(serialized)

        all_identical = all(s == samples[0] for s in samples)

        return DeterminismResult(
            is_deterministic=all_identical,
            iterations=self.sample_iterations,
            variance_detected=not all_identical,
            output_samples=samples[:2],
        )
