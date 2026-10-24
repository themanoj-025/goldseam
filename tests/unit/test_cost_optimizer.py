"""Unit tests for CostOptimizer."""

from goldseam.llm.cost_optimizer import CostOptimizer


def test_cost_optimizer_within_budget() -> None:
    events = [f"event {i}" for i in range(20)]
    pruned, report = CostOptimizer.optimize_trace_events(events, max_events=50)
    assert len(pruned) == 20
    assert report.tokens_saved_estimate == 0
    assert report.dollars_saved_estimate == 0.0


def test_cost_optimizer_pruning() -> None:
    events = [f"event {i}" for i in range(200)]
    pruned, report = CostOptimizer.optimize_trace_events(events, max_events=30)
    assert len(pruned) <= 32
    assert report.original_event_count == 200
    assert report.tokens_saved_estimate > 0
    assert report.dollars_saved_estimate > 0.0
    assert report.recommended_model_tier == "cost_efficient"
    assert "[TRUNCATED REPETITIVE INTERMEDIATE STDOUT...]" in pruned
