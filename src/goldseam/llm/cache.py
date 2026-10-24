"""Content-addressed, privacy-preserving disk and memory cache for LLM completions."""

import hashlib
import json
from pathlib import Path
from typing import Any


class LLMCache:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_store: dict[str, dict[str, Any]] = {}

    def _compute_key(self, prompt: str, model_id: str, schema_json: str) -> str:
        h = hashlib.sha256()
        h.update(model_id.encode("utf-8"))
        h.update(schema_json.encode("utf-8"))
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()

    def get(self, prompt: str, model_id: str, schema_json: str) -> dict[str, Any] | None:
        key = self._compute_key(prompt, model_id, schema_json)
        if key in self.memory_store:
            return self.memory_store[key]

        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.is_file():
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        self.memory_store[key] = data
                        return data
                except Exception:
                    return None
        return None

    def put(self, prompt: str, model_id: str, schema_json: str, response_data: dict[str, Any]) -> None:
        key = self._compute_key(prompt, model_id, schema_json)
        self.memory_store[key] = response_data

        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            try:
                cache_file.write_text(json.dumps(response_data, indent=2), encoding="utf-8")
            except Exception:
                pass
