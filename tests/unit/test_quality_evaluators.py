"""Unit tests for coverage, mutation, and determinism evaluators."""

from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.quality.coverage import CoverageEvaluator
from goldseam.quality.determinism import DeterminismEvaluator
from goldseam.quality.mutation import MutationEvaluator


def test_coverage_and_mutation_evaluators() -> None:
    bundle = GeneratedBundle(
        skill_slug="calc-tool",
        files=[
            GeneratedFile(path="SKILL.md", content="---\nname: calc-tool\ndescription: Calc.\n---\n# Tool\n## When to Use\n## When Not to Use\n## Steps\n## Examples"),
            GeneratedFile(path="scripts/calc.py", content="def add(a, b):\n    if a > 0:\n        return a + b\n    return b\n"),
            GeneratedFile(path="tests/test_calc.py", content="def test_add():\n    assert add(1, 2) == 3\n    assert add(-1, 2) == 2\n    assert add(0, 5) == 5\n    assert add(2, 2) == 4\n"),
        ],
    )

    cov_eval = CoverageEvaluator(target_threshold_percent=70.0)
    cov_rep = cov_eval.evaluate_bundle_coverage(bundle)
    assert cov_rep.total_statements > 0
    assert cov_rep.coverage_percent >= 70.0

    mut_eval = MutationEvaluator(target_threshold_percent=70.0)
    mut_rep = mut_eval.evaluate_mutations(bundle)
    assert mut_rep.mutations_generated > 0
    assert mut_rep.mutation_score_percent >= 70.0


def test_determinism_evaluator() -> None:
    det_eval = DeterminismEvaluator(sample_iterations=5)

    def stable_fn(x: int) -> dict[str, int]:
        return {"val": x * 2}

    res_stable = det_eval.evaluate_callable(stable_fn, (5,))
    assert res_stable.is_deterministic is True
    assert res_stable.variance_detected is False
