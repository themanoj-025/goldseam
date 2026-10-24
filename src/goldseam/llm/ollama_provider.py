"""Local Ollama provider adapter for offline zero-cost execution."""

import json
import urllib.error
import urllib.request
from typing import TypeVar

from pydantic import BaseModel

from goldseam.errors import LLMProviderError
from goldseam.llm.base import LLMClient, LLMResponse

T = TypeVar("T", bound=BaseModel)


class OllamaClient(LLMClient):
    name = "ollama"

    def __init__(self, model_id: str = "llama3.2:latest", base_url: str = "http://localhost:11434") -> None:
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")

    def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        url = f"{self.base_url}/api/chat"
        schema = response_model.model_json_schema()
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": "You are a compiler emitting strictly formatted JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            "format": schema,
            "stream": False,
            "options": {"temperature": temperature},
        }

        if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
            raise LLMProviderError("Ollama base_url must start with http:// or https://")

        req = urllib.request.Request(  # noqa: S310
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
                content_str = data.get("message", {}).get("content", "{}")
                parsed_json = json.loads(content_str)
                parsed_obj = response_model.model_validate(parsed_json)

                p_tokens = data.get("prompt_eval_count", 0)
                c_tokens = data.get("eval_count", 0)

                return LLMResponse(
                    content=parsed_obj,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    cost_usd=0.0,  # Local inference has 0 cloud cost
                    model_id=self.model_id,
                )
        except urllib.error.URLError as err:
            raise LLMProviderError(f"Ollama server unreachable at '{self.base_url}': {err}") from err
        except Exception as err:
            raise LLMProviderError(f"Ollama structured completion failed: {err}") from err
