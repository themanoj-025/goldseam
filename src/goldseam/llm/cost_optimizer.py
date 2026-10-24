"""Cost optimizer for pruning redundant trace frames and optimizing model routing spend."""

from pydantic import BaseModel


class CostOptimizationReport(BaseModel):
    original_event_count: int
    optimized_event_count: int
    tokens_saved_estimate: int
    dollars_saved_estimate: float
    recommended_model_tier: str


class CostOptimizer:
    """Optimizes input context size and model tier selection to conserve token budgets."""

    @classmethod
    def optimize_trace_events(
        cls,
        events: list[str],
        max_events: int = 50,
        estimated_cost_per_1k_tokens: float = 0.003,
    ) -> tuple[list[str], CostOptimizationReport]:
        original_count = len(events)
        if original_count <= max_events:
            return events, CostOptimizationReport(
                original_event_count=original_count,
                optimized_event_count=original_count,
                tokens_saved_estimate=0,
                dollars_saved_estimate=0.0,
                recommended_model_tier="standard",
            )

        # Retain head (initiating prompt/command) and tail (error message/stack trace)
        head_count = max_events // 3
        tail_count = max_events - head_count
        pruned = events[:head_count] + ["[TRUNCATED REPETITIVE INTERMEDIATE STDOUT...]"] + events[-tail_count:]

        pruned_count = len(pruned)
        dropped_events = original_count - pruned_count
        tokens_saved = dropped_events * 50  # Average ~50 tokens per line
        dollars_saved = round((tokens_saved / 1000.0) * estimated_cost_per_1k_tokens, 4)

        report = CostOptimizationReport(
            original_event_count=original_count,
            optimized_event_count=pruned_count,
            tokens_saved_estimate=tokens_saved,
            dollars_saved_estimate=dollars_saved,
            recommended_model_tier="cost_efficient",
        )
        return pruned, report
