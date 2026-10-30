# Ingestion Adapters

Goldseam accepts untrusted inputs across diverse developer and agent environments through specialized adapters.

---

## 1. Supported Adapters

| Adapter | CLI Flag | Source Identifier | Primary Format |
| :--- | :--- | :--- | :--- |
| **Terminal Log** | `--from-log` | `terminal` | Plain stdout/stderr logs, shell error streams, ANSI colored output |
| **Pytest Log** | `--from-log` | `pytest_log` | Pytest failure summaries, assertion diffs, captured stderr |
| **Python Traceback** | `--from-log` | `traceback_py` | Standard Python stack traces with exception signatures |
| **Claude Code JSONL** | `--from-transcript`| `claude_code_jsonl` | Claude Code JSONL transcripts containing user prompts, tool calls, and results |
| **Git Diff** | `--from-diff` | `git_diff` | Unified diffs representing before/after human code corrections |
| **Plain Need** | `--need` | `plain_need` | Free-text human requirements (e.g. "Validate ISO-8601 dates") |
| **Streaming Stdin** | `--from-stdin` | `stdin` | Piped logs streamed line-by-line (handles up to 50MB logs) |

---

## 2. Ingestion & Sanitization Pipeline

Each adapter executes:
1. **Size Bounding:** Caps incoming input at 50MB and max 10,000 trace events to prevent memory exhaustion.
2. **ANSI & Path Hygiene:** Strips color codes and normalizes Windows backslashes into standard forward slashes.
3. **Secret Redaction:** Strips API tokens, private keys, connection URIs, and user directories before persisting to the run store.
4. **Signature Extraction:** Generates a canonical error signature used for library deduplication and clustering.
