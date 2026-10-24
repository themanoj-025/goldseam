"""OpenAI provider adapter supporting structured outputs."""

import os
from typing import TypeVar

from pydantic import BaseModel

from goldseam.errors import LLMProviderError
from goldseam.llm.base import LLMClient, LLMResponse

T = TypeVar("T", bound=BaseModel)


class OpenAIClient(LLMClient):
    name = "openai"

    def __init__(self, model_id: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        if not self.api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured.")

        try:
            import openai
        except ImportError as e:
            raise LLMProviderError("The 'openai' package is not installed. Install via `uv add openai`.") from e

        client = openai.OpenAI(api_key=self.api_key)
        try:
            completion = client.beta.chat.completions.parse(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are an expert compiler synthesizing verified Agent Skills."},
                    {"role": "user", "content": prompt},
                ],
                response_format=response_model,
                temperature=temperature,
            )
            parsed_obj = completion.choices[0].message.parsed
            if parsed_obj is None:
                raise LLMProviderError("OpenAI returned empty structured output.")

            usage = completion.usage
            p_tokens = usage.prompt_tokens if usage else 0
            c_tokens = usage.completion_tokens if usage else 0
            # Approximate pricing
            cost = (p_tokens * 0.15 + c_tokens * 0.60) / 1_000_000

            return LLMResponse(
                content=parsed_obj,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                cost_usd=round(cost, 6),
                model_id=self.model_id,
            )
        except Exception as err:
            raise LLMProviderError(f"OpenAI API request failed: {err}") from err
