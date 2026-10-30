"""Tests for json-stream-parser tool."""

from scripts.parse_stream import parse_json_stream


def test_parse_json_stream() -> None:
    data = '{"name": "alpha"}{"name": "beta"}'
    items = parse_json_stream(data)
    assert len(items) == 2
    assert items[0]["name"] == "alpha"
    assert items[1]["name"] == "beta"


def test_parse_empty_stream() -> None:
    assert parse_json_stream("") == []
