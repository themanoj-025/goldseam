# Goldseam Concepts

Goldseam formalizes autonomous failure recovery by treating agent runtime failures as structured capability gaps that can be triaged, specified, tested, synthesized, and verified.

---

## 1. Failure-to-Skill Paradigm

When an AI agent fails on a repetitive task (e.g. malformed JSON streams, ambiguous CSV delimiters, or Windows path escapes), the typical recourse is manual human debugging or non-reusable prompt tweaking.

Goldseam automates capability compilation:
```
Failure Trace -> Redaction -> Triage -> SkillSpec -> Code + Tests -> Docker Sandbox -> Human Review -> Signed Skill
```

---

## 2. Core Abstractions

### Route
Every incident is triaged into one of five deterministic targets:
- **`SKILL`**: Multi-file capability packaging a spec-pure `SKILL.md`, reusable Python tools, independent regression tests, and cryptographic provenance.
- **`SCRIPT`**: Standalone single-file deterministic utility script.
- **`MCP_TOOL`**: Interactive tool exposed via the Model Context Protocol stdio interface.
- **`RULE_ONLY`**: Procedural preference or instruction requiring no executable code (emits markdown guidelines).
- **`DISCARD`**: Transient error (e.g., 503 HTTP outage, host disk full, typo) unsuitable for automated skill generation.

### Trace & Redaction
Raw traces are untrusted. Before any analysis or external model calls:
- All high-entropy tokens, AWS/GitHub/OpenAI API keys, connection strings, IPs, emails, and home paths are replaced with deterministic stable placeholders (e.g., `[REDACTED_API_KEY_1]`).
- ANSI escape sequences and platform line endings (`\r\n` vs `\n`) are normalized.
- Potential prompt injection vectors (role-spoofing markers, command injections) are quarantined.

### SkillSpec Contract
The model never generates code directly from an untrusted trace. Instead, it first designs a typed `SkillSpec`:
- **Triggers**: Activation keywords and semantic intent phrases.
- **Non-Triggers**: Scenarios where the skill must not execute.
- **Tool Specs**: Function name, docstring, JSON Schemas for input/output parameters, declared side effects (`NONE`, `READ_WORKSPACE`, `WRITE_WORKSPACE`, `NETWORK`), and preconditions.
- **Examples**: Minimum of 3 concrete input/output test examples, with at least 1 negative error-handling case.

### Independent Test Oracles & Replay Anchors
- **Independence:** Test suites are derived strictly from the `SkillSpec` contract and the sanitized failure replay anchor, never from the generated code itself.
- **Replay Anchor:** A cryptographically locked input/output snapshot reproducing the original incident. During self-repair, the anchor is strictly immutable.

### Provenance & Tamper Detection
- Every generated skill folder includes `provenance.json` containing SHA-256 hashes of all artifacts (`SKILL.md`, `scripts/*.py`, `tests/*.py`, `goldseam.manifest.json`).
- `goldseam verify <skill>` re-calculates the canonical hash tree and immediately flags single-byte modifications or untracked additions.
