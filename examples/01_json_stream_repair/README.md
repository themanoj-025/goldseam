# Example 1: JSON Stream Repair

## Overview
When agents or APIs stream unbracketed, concatenated JSON objects (e.g. `{"id": 1}{"id": 2}`), standard `json.loads` raises `ValueError: Extra data: line 1 column 15 (char 14)`.

Goldseam ingests this trace, triages the capability gap, and synthesizes a deterministic stream parser skill.

## Running this example
```bash
goldseam build --from-log examples/01_json_stream_repair/input_trace.log --dry-run
```
