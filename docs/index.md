# Goldseam

**Failure-to-Skill Compiler for Autonomous AI Agents**

Goldseam ingests untrusted agent traces, logs, transcripts, and developer corrections; diagnoses reusable capability gaps; synthesizes typed `SkillSpec` contracts; generates spec-conformant Agent Skills and MCP tool servers; derives independent regression tests with immutable replay oracles; verifies untrusted code in a constrained sandbox; executes bounded self-repair; and packages with cryptographic provenance.

---

## Key Invariants

1. **Untrusted Generated Code Never Imported/Executed in Trusted Process:** Isolation via hardened Docker containers (`--network none`, `--read-only`, `--cap-drop ALL`).
2. **Fail-Closed Gate:** If sandbox containment is offline or unreachable, installation reports `BLOCKED`.
3. **Immutable Replay Oracles:** Anchor fixtures are locked via content hashes and cannot be modified during self-repair.
4. **Independent Test Derivation:** Regression tests are derived from formal specifications and failure anchors, never from generated code.
5. **No Blind Trust in Model Output:** Risk assessments and policy decisions are computed by deterministic policy engines, never inferred from model assertions.

---

## Quick Navigation

- [Quickstart Guide](getting-started/quickstart.md) — 3-command setup and trial run
- [Core Concepts](getting-started/concepts.md) — Architectural taxonomy (Route, Trace, SkillSpec, ReplayOracle)
- [System Architecture](architecture/overview.md) — Multi-stage compilation pipeline & state machine
- [Threat Model](security/threat-model.md) — STRIDE security model & sandbox invariants
- [CLI Reference](reference/cli.md) — Complete command documentation
- [Benchmark Science](benchmarks/methodology.md) — 42 golden benchmarks and ablation studies
- [Architecture Decisions](adr/index.md) — Key engineering decisions and ADRs
