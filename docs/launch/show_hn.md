# Show HN: Goldseam – A Failure-to-Skill Compiler for AI Agents

**Link / Repo:** https://github.com/themanoj-025/goldseam

Hey HN,

When coding agents and autonomous workflows fail, the standard approach is either to retry blindly or hope a human pastes a fix into prompt context. But most failures are recurring capability gaps—like missing Unicode normalizers, unbracketed JSON stream parsing, dialect-incompatible CSV delimiters, or Windows path reserved stems.

We built **Goldseam**: an autonomous, verified failure-to-skill compiler.

### What it does:
1. **Ingests untrusted traces:** Terminal logs, Pytest failures, Python tracebacks, or unified Git diffs.
2. **Redacts & Sanitizes:** Automatically scrubs API keys, JWTs, and high-entropy secrets, and flags adversarial prompt injections (`ignore instructions`, `curl exfiltration`, `subprocess`).
3. **Triages & Routes:** Categorizes the failure into `SKILL` (reusable capability), `RULE_ONLY` (procedural/style guidance), or `DISCARD` (transient 503 or typo).
4. **Designs typed contracts:** Generates strict `SkillSpec` contracts with Pydantic JSON schemas and >=3 examples including negative failure modes.
5. **Generates spec-pure Agent Skills:** Creates compliant `SKILL.md` files (conforming to `agentskills.io`), deterministic Python tools, and optional MCP stdio servers.
6. **Sandboxes & Verifies:** Runs independent test generation inside an isolated sandbox. AST allowlists inspect imports before container execution.
7. **Attests Provenance:** Cryptographically signs file artifact hashes into `provenance.json`. `goldseam verify` detects single-byte tampering instantly.

Everything is offline-capable via FakeLLM/Ollama, strictly typed, and evaluated against a 42-case golden benchmark with hidden oracles.

We'd love your feedback, criticism on our threat model, and contributions!
