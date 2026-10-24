# Agent Skills Specification & Goldseam Conformance Contract

**Specification Baseline:** Agent Skills Protocol v1.0  
**Retrieval & Verification Date:** 2026-10-24  
**Status:** Pinned & Verified against Static Linter (`src/goldseam/security/skillmd_lint.py`)  

---

## 1. Specification Overview

The **Agent Skill** specification defines an autonomous capability bundle consumable by AI coding assistants, autonomous agents, and tool execution engines (including Claude Code, Google Antigravity, and OpenAI agents).

Each skill is a self-contained directory containing:
1. `SKILL.md` — The canonical natural language trigger, instructions, and human-readable contract.
2. `scripts/` — Deterministic, pure-function Python executables callable by agents.
3. `tests/` — Independently generated pytest suites verifying positive, negative, and edge-case execution.
4. `goldseam.manifest.json` — Structured capability declaration (JSON Schema inputs/outputs, declared side-effects, permitted imports, risk level).
5. `provenance.json` — Cryptographic SHA-256 tamper-detection attestation and compilation chain-of-custody.

---

## 2. SKILL.md Frontmatter Rules

In strict conformance with the specification:
- **Allowed Frontmatter Fields:** `name` (slug format: `^[a-z0-9]+(-[a-z0-9]+)*$`, length 1–64) and `description` (non-empty summary).
- **Prohibited Frontmatter Fields:** Non-standard attributes such as `tools:`, `version:`, `scripts:`, `author:`, or executable hooks must **never** appear in the YAML frontmatter. These structured metadata belongs strictly in `goldseam.manifest.json`.
- Enforced by: `goldseam.security.skillmd_lint.SkillMdLinter`.

### Canonical Frontmatter Example
```yaml
---
name: json-stream-parser
description: Parses and repairs malformed streaming JSON lines with truncated closing delimiters.
---
```

---

## 3. SKILL.md Required Markdown Sections

The body of `SKILL.md` must contain structured guidance to prevent model hallucinations and unintended tool invocation:

| Section Heading | Required Content |
| :--- | :--- |
| `# <Skill Title>` | Concise H1 title matching skill intent. |
| `## When to use` | Concrete trigger situations, matching keywords, and failure symptoms. |
| `## When not to use` | Explicit negative boundaries, disclaimers, and handoffs to alternative tools. |
| `## Preconditions` | Required system state, files, or environment configurations. |
| `## Steps` | Step-by-step procedural guidelines for an agent invoking the script. |
| `## Examples` | Concrete before/after execution examples with exact argument syntax. |
| `## Failure modes` | Expected exit codes, error messages, and recovery procedures. |
| `## Safety notes` | Declared security restrictions (e.g. read-only, no network access). |

---

## 4. Script & Execution Contract

All executables placed in `scripts/` must adhere to:
1. **Pure Core Function:** A single primary function with strict typing, deterministic transformation logic, and zero ambient global side effects.
2. **CLI Entrypoint (`main`):** Reads standard JSON input from `stdin` or argument list, emits JSON payload `{"result": ...}` to `stdout` with exit code `0`, and emits `{"error": ...}` to `stderr` with exit code `1` upon failure.
3. **No Unrestricted Imports:** Modules must strictly comply with the active `policy.toml` allowlist. Untrusted dynamic evaluation (`eval`, `exec`, `__import__`) is strictly rejected.

---

## 5. Manifest & Cryptographic Provenance

- **`goldseam.manifest.json`:** Stores tool schemas, declared side-effects (`NONE`, `READ_WORKSPACE`, `WRITE_WORKSPACE`, `NETWORK`), and trusted risk assessments (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **`provenance.json`:** Contains the SHA-256 hash tree of all files in the skill directory (excluding `provenance.json` itself). Any single-byte modification invalidates verification (`goldseam verify`).
