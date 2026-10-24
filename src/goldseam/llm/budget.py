"""Budget tracker for token consumption and USD spend."""

from goldseam.errors import BudgetExceededError


class BudgetTracker:
    def __init__(self, max_budget_usd: float = 1.00, max_tokens: int = 500000) -> None:
        self.max_budget_usd = max_budget_usd
        self.max_tokens = max_tokens
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    def record_usage(self, prompt_tokens: int, completion_tokens: int, cost_usd: float) -> None:
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_usd += cost_usd

        if self.total_cost_usd > self.max_budget_usd:
            raise BudgetExceededError(
                f"LLM spend (${self.total_cost_usd:.4f}) exceeded configured maximum budget (${self.max_budget_usd:.2f})"
            )

        if self.total_tokens > self.max_tokens:
            raise BudgetExceededError(
                f"LLM token consumption ({self.total_tokens}) exceeded maximum token limit ({self.max_tokens})"
            )
