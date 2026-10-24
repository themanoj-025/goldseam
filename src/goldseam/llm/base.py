"""Abstract base client and response contracts for LLM providers."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content: T
    prompt_tokens: int = Field(ge=0, default=0)
    completion_tokens: int = Field(ge=0, default=0)
    cost_usd: float = Field(ge=0.0, default=0.0)
    model_id: str = Field(default="unknown")


class LLMClient(ABC):
    name: str

    @abstractmethod
    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        """Sends prompt and parses model output into validated Pydantic model T."""
