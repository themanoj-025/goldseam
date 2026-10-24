---
name: json-stream-parser
description: Parses streams of unbracketed concatenated JSON objects into structured lists.
---

# json-stream-parser

## When to Use
- When dealing with logs or HTTP chunk streams outputting adjacent JSON dictionaries without array brackets.
- When `json.loads` fails with `ValueError: Extra data`.

## When Not to Use
- When input is standard bracketed JSON arrays `[...]`.
- When payload is arbitrary unstructured plain text.

## Steps
1. Feed the raw string payload into the parser.
2. Iteratively parse successive JSON tokens using `JSONDecoder.raw_decode`.
3. Collect and emit the array of decoded dictionary objects.

## Examples
- Input: `{"a": 1}{"b": 2}` -> Output: `[{"a": 1}, {"b": 2}]`
