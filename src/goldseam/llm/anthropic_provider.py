"""Anthropic provider adapter supporting structured outputs via tool definition."""

import os
from typing import Any, TypeVar

from pydantic import BaseModel

from goldseam.errors import LLMProviderError
from goldseam.llm.base import LLMClient, LLMResponse

T = TypeVar("T", bound=BaseModel)


class AnthropicClient(LLMClient):
    name = "anthropic"

    def __init__(self, model_id: str = "claude-3-5-sonnet-20241022", api_key: str | None = None) -> None:
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        if not self.api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY is not configured.")

        try:
            import anthropic
        except ImportError as e:
            raise LLMProviderError("The 'anthropic' package is not installed. Install via `uv add anthropic`.") from e

        client = anthropic.Anthropic(api_key=self.api_key)
        tool_schema = response_model.model_json_schema()
        tool_name = f"record_{response_model.__name__.lower()}"

        try:
            req_kwargs: dict[str, Any] = {
                "model": self.model_id,
                "max_tokens": 4096,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                "tools": [
                    {
                        "name": tool_name,
                        "description": f"Record structured {response_model.__name__}",
                        "input_schema": tool_schema,
                    }
                ],
                "tool_choice": {"type": "tool", "name": tool_name},
            }
            message = client.messages.create(**req_kwargs)

            tool_input = None
            for block in message.content:
                if block.type == "tool_use" and block.name == tool_name:
                    tool_input = block.input
                    break

            if tool_input is None:
                raise LLMProviderError("Anthropic did not return expected tool call block.")

            parsed_obj = response_model.model_validate(tool_input)
            usage = message.usage
            p_tokens = usage.input_tokens if usage else 0
            c_tokens = usage.output_tokens if usage else 0
            cost = (p_tokens * 3.0 + c_tokens * 15.0) / 1_000_000

            return LLMResponse(
                content=parsed_obj,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                cost_usd=round(cost, 6),
                model_id=self.model_id,
            )
        except Exception as err:
            raise LLMProviderError(f"Anthropic API request failed: {err}") from err
