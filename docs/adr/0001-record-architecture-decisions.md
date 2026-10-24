# 1. Architectural Decisions and Principles

Date: 2026-10-24

## Status
Accepted

## Context
Goldseam is an autonomous failure-to-skill compiler. When agents fail, fail-to-recover loops waste model tokens and context windows. The core objective is turning empirical failures into verifiable, reusable Agent Skills, deterministic Python tools, and Model Context Protocol (MCP) servers. However, compiling code from untrusted traces and LLM outputs introduces critical security, stability, and correctness challenges:
1. Untrusted generated code can escape, execute arbitrary commands, or leak host environment secrets.
2. Models can self-report that their generated code is "safe" or "tested" when it is not.
3. Repaired code might alter or weaken the tests themselves to make test suites artificially pass.
4. Generated skills might not conform to the emerging open Agent Skills standard (`SKILL.md`).

## Decisions
1. **Pydantic v2 with `extra="forbid"`:** All trust boundary contracts strictly forbid unknown attributes to prevent prototype pollution and prompt-injection-driven schema abuse.
2. **Deterministic Risk Assessment:** The security risk rating (LOW, MEDIUM, HIGH, CRITICAL) is calculated by code through AST analysis and side-effect declarations, rejecting model self-attested risk.
3. **Fail-Closed Container Sandbox:** Untrusted code execution requires container isolation (read-only root filesystem, no network, dropped Linux capabilities). If Docker is offline, execution is marked `BLOCKED`. A local subprocess runner is only permitted for trusted fixtures when explicitly requested with `--allow-weak-sandbox`.
4. **Independent Test Synthesis & Frozen Anchors:** Test generation derives assertions purely from the typed `SkillSpec` before implementation generation. Replay fixtures and oracle tests are cryptographically hashed; self-repair routines cannot modify tests.
5. **Spec-Pure `SKILL.md`:** `SKILL.md` frontmatter adheres strictly to the `agentskills.io` specification (only standard fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Technical manifests, JSON schemas, and provenance hashes reside in `goldseam.manifest.json`.
6. **Pure Core Function Architecture:** Tools are generated with a pure, deterministic Python core function and a clean CLI wrapper that accepts JSON, returns JSON, and produces nonzero exit codes on error. This core function is directly reusable by the MCP emitter.

## Consequences
- Requires Docker for production code verification.
- Enforces strict review gates before installing capabilities into live environments.
- Completely prevents test-tampering during iterative repair loops.
