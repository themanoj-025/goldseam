# Goldseam Enforceable Invariants

This file establishes mandatory engineering and security invariants for autonomous coding agents, contributors, and systems executing within the Goldseam repository.

## Invariant 1: Untrusted Generated Code Isolation
Untrusted generated code, scripts, or tests must **never** be imported, loaded via `importlib`, or executed directly within the trusted host Python interpreter process. All untrusted executions must be dispatched to an isolated sandbox backend.

## Invariant 2: Mandatory Trace Redaction
No raw input logs, terminal dumps, or transcripts may be transmitted to external LLM providers or saved to long-term storage without prior redaction of credentials, API tokens, private keys, IP addresses, usernames, and sensitive home paths.

## Invariant 3: Sandbox Fail-Closed
Sandbox environments must operate fail-closed. If container isolation or requisite security controls (e.g. read-only root, no network, dropped capabilities) cannot be verified, the execution must immediately return `BLOCKED`. A weak sandbox (such as a local subprocess) may only be used if explicitly permitted by configuration for trusted development fixtures, and must never be represented as secure.

## Invariant 4: Immutable Replay Oracles & Test Derivation
Tests must be derived independently from the typed `SkillSpec` and problem contract, never synthesized post-hoc from generated implementation code. Replay oracle fixtures and anchor tests are cryptographically hashed and immutable during repair cycles; repair engines are strictly prohibited from mutating or deleting tests to achieve a passing state.

## Invariant 5: Trusted Deterministic Risk Assessment
Risk levels (e.g. LOW, MEDIUM, HIGH, CRITICAL) must be evaluated and assigned by a trusted deterministic security policy based on declared capabilities, AST inspection, side-effects, and file interactions. Model self-reports of safety or risk are strictly untrusted.

## Invariant 6: Mandatory Human Approval Prior to Live Installation
The compiler may propose, stage, and verify skills autonomously, but installation of executable tools or skills into active user or agent environments requires explicit, documented human authorization.

## Invariant 7: Offline Deterministic Testability
All core suites, parsers, triage rules, test generators, security linters, and verification gates must execute and pass offline without live network access or paid external API keys, utilizing the deterministic `FakeLLM` adapter and recorded test fixtures.

## Invariant 8: Cross-Platform Path Hygiene
Code must handle Windows, macOS, and Linux paths cleanly. Path traversal attempts (`../`, `..\`), absolute host paths, device names (`CON`, `PRN`, `AUX`, `NUL`), and symlink attacks must be rejected unconditionally.

## Invariant 9: Strict Static Typing & Schema Integrity
All data contracts across pipeline boundaries must use Pydantic v2 models with `extra="forbid"`. Code must pass strict `mypy` type checking with zero errors and no implicit `Any` annotations at interface boundaries.

## Invariant 10: No Silent Success & No Unverifiable Security Claims
Every stage output, test outcome, and security finding must be explicitly recorded. Missing gates produce `BLOCKED`, not `PASS`. Security capabilities must be honestly documented; AST checks must be described as heuristic filtering rather than absolute escape prevention.
