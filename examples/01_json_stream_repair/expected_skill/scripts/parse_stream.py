"""Deterministic JSON stream parser tool."""

from json import JSONDecoder
from typing import Any


def parse_json_stream(raw_text: str) -> list[dict[str, Any]]:
    decoder = JSONDecoder()
    pos = 0
    results: list[dict[str, Any]] = []
    text = raw_text.strip()
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        obj, end_pos = decoder.raw_decode(text, idx=pos)
        results.append(obj)
        pos = end_pos
    return results
