---
name: csv-delimiter-detector
description: Inspects raw tabular text and reliably detects the field delimiter character.
---

# csv-delimiter-detector

## When to Use
- When importing tabular data files without known separator formatting.
- When `csv.Sniffer` fails or encounters ambiguous multi-delimiter samples.

## When Not to Use
- When the delimiter is already explicitly declared in schemas or configuration.

## Steps
1. Scan the header line and sample lines for candidate separators (`,`, `\t`, `;`, `|`).
2. Score delimiter consistency across multiple rows.
3. Return the highest-scoring candidate separator.
