# Goldseam Implementation Matrix

This ledger maps each system requirement to its implementing files, associated test suites, verifiable evidence, and real-time execution status (`PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`).

| Req ID | Description | Source Files | Test Files | Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-P0-01** | Workspace audit, toolchain verification (uv, Python 3.12, git) | `pyproject.toml`, `uv.lock` | CLI execution | `uv --version`, `python 3.12` | PASS |
| **REQ-P0-02** | Official Agent Skills & MCP spec verification & documentation | `docs/spec/`, `docs/threat-model.md` | Search & validation | Spec summaries in docs | PASS |
| **REQ-P0-03** | Enforceable invariants constitution (`AGENTS.md`, `CLAUDE.md`) | `AGENTS.md`, `CLAUDE.md` | Doc verification | Identical invariants | PASS |
| **REQ-P0-04** | Execution ledger, blockers & status tracking | `docs/*.md` | Doc verification | Persistent tracking | PASS |
| **REQ-P1-01** | Versioned Pydantic v2 data models (`Route`, `SideEffect`, `TraceEvent`, `SkillSpec`, etc.) | `src/goldseam/models/*.py` | `tests/unit/test_models.py` | 5 passed tests | PASS |
| **REQ-P1-02** | Spec-pure `SKILL.md` parser, renderer, validator | `src/goldseam/security/skillmd_lint.py`, `src/goldseam/registry/templates.py` | `tests/unit/test_skillmd.py` | 4 passed tests | PASS |
| **REQ-P1-03** | Configuration precedence & environment resolution | `src/goldseam/config.py` | `tests/unit/test_config.py` | 3 passed tests | PASS |
| **REQ-P1-04** | Atomic, privacy-preserving run store | `src/goldseam/telemetry/run_store.py` | `tests/unit/test_run_store.py` | 3 passed tests | PASS |
| **REQ-P2-01** | Security policy definition & TOML parser | `src/goldseam/security/policy.toml`, `src/goldseam/security/import_policy.py` | `tests/security/test_policy.py` | 3 passed tests | PASS |
| **REQ-P2-02** | AST visitor for import, call, and attribute allowlisting | `src/goldseam/security/ast_visitor.py` | `tests/security/test_ast_visitor.py` | 5 passed tests | PASS |
| **REQ-P2-03** | High-entropy secrets and credential scanner | `src/goldseam/security/secrets_scan.py` | `tests/security/test_secrets_scan.py` | 3 passed tests | PASS |
| **REQ-P2-04** | Adversarial bypass corpus (100+ AST bypass snippets) | `tests/security/bypass_corpus/` | `tests/security/test_bypass_corpus.py` | 105/105 caught | PASS |
| **REQ-P3-01** | Hardened Docker sandbox runner (non-root, read-only root, no network) | `src/goldseam/sandbox/backends/docker.py`, `docker/*` | `tests/security/test_docker_sandbox.py` | Fail-closed BLOCKED check | PASS |
| **REQ-P3-02** | Weak local subprocess sandbox (fail-closed, explicit opt-in only) | `src/goldseam/sandbox/backends/local.py` | `tests/unit/test_local_sandbox.py` | 3 passed tests | PASS |
| **REQ-P3-03** | Staging environment, path hygiene & symlink protection | `src/goldseam/sandbox/temp_env.py` | `tests/unit/test_temp_env.py` | Traversal rejection tests | PASS |
| **REQ-P4-01** | LLM client abstraction, FakeLLM, and provider adapters | `src/goldseam/llm/*.py` | `tests/unit/test_llm.py` | 3 passed tests | PASS |
| **REQ-P4-02** | Multi-source trace ingest adapters (logs, tracebacks, diffs, plain needs) | `src/goldseam/ingest/*.py` | `tests/unit/test_ingest.py` | 4 passed tests | PASS |
| **REQ-P4-03** | PII and credential redactor with stable placeholders | `src/goldseam/ingest/redact.py` | `tests/unit/test_redact.py` | 3 passed tests | PASS |
| **REQ-P4-04** | Triage and capability router (SKILL, SCRIPT, MCP, RULE_ONLY, DISCARD) | `src/goldseam/core/triage.py`, `src/goldseam/core/router.py` | `tests/unit/test_triage.py` | 3 passed tests | PASS |
| **REQ-P5-01** | SkillSpec designer from normalized trace | `src/goldseam/core/spec_designer.py` | `tests/unit/test_spec_designer.py` | 2 passed tests | PASS |
| **REQ-P5-02** | Spec-driven code generator (Python CLI & pure functions) | `src/goldseam/core/generator.py` | `tests/unit/test_generator.py` | 2 passed tests | PASS |
| **REQ-P5-03** | Independent test generator with immutable replay anchors | `src/goldseam/core/testgen.py` | `tests/unit/test_testgen.py` | 2 passed tests | PASS |
| **REQ-P5-04** | Claims audit & trigger evaluation engine | `src/goldseam/quality/claims_audit.py`, `src/goldseam/quality/trigger_eval.py` | `tests/unit/test_quality.py` | 3 passed tests | PASS |
| **REQ-P6-01** | Durable state machine orchestrator with crash resumption | `src/goldseam/core/orchestrator.py` | `tests/integration/test_orchestrator.py` | 3 passed tests | PASS |
| **REQ-P6-02** | Bounded self-repair engine with oscillation detection | `src/goldseam/core/repair.py` | `tests/integration/test_repair.py` | 2 passed tests | PASS |
| **REQ-P7-01** | Cryptographic provenance attestation & tamper detection | `src/goldseam/registry/provenance.py` | `tests/unit/test_index.py` | 1-byte tamper detection | PASS |
| **REQ-P7-02** | Atomic packager with collision handling & rollback | `src/goldseam/registry/packager.py` | `tests/unit/test_index.py` | Atomic install & rollback | PASS |
| **REQ-P7-03** | Standalone MCP stdio tool emitter | `src/goldseam/registry/mcp_emitter.py` | `tests/integration/test_mcp.py` | Smoke test | PASS |
| **REQ-P8-01** | Typer & Rich CLI (`init`, `doctor`, `build`, `verify`, `review`, etc.) | `src/goldseam/cli.py` | `tests/integration/test_cli.py` | 8 passed CLI tests | PASS |
| **REQ-P9-01** | 40+ synthetic benchmark cases with hidden test oracles | `benchmarks/` | `tests/integration/test_bench.py` | 42 cases, 97.6% triage | PASS |
| **REQ-P10-01**| CI workflows (GitHub Actions, multi-OS matrix, CodeQL) | `.github/workflows/*.yml` | Packaging & workflow files | Wheel & sdist built | PASS |
| **REQ-P4-05**| Claude Code JSONL & 50MB log streaming ingest | `src/goldseam/ingest/claude_code_jsonl.py` | `tests/unit/test_claude_jsonl.py`, `test_streaming_large_log.py` | 2 passed tests | PASS |
| **REQ-P4-06**| LLM provider adapters (OpenAI, Anthropic, Ollama) & cache | `src/goldseam/llm/*.py` | `tests/unit/test_llm.py` | Unit tests & mock adapters | PASS |
| **REQ-P5-05**| Failure analyzer & versioned prompt catalog | `src/goldseam/core/analyzer.py`, `prompts/v1/` | `tests/unit/test_analyzer.py` | Prompt & root cause tests | PASS |
| **REQ-P7-04**| Semver comparator & breaking change detector | `src/goldseam/registry/versioning.py` | `tests/unit/test_versioning.py` | Semver bump tests | PASS |
| **REQ-P7-05**| Goldseam MCP Server with tool discovery & verify | `src/goldseam/registry/mcp_server.py` | `tests/unit/test_mcp_server.py` | FastMCP smoke test | PASS |
| **REQ-P9-02**| Quality evaluators (coverage, mutation, determinism) | `src/goldseam/quality/*.py` | `tests/unit/test_quality_evaluators.py` | Coverage & mutation tests | PASS |
| **REQ-P10-02**| CI/PR proposal automation workflow | `.github/workflows/goldseam-proposal-pr.yml` | Workflow schema verification | Proposal PR workflow | PASS |
| **REQ-P11-02**| Fast agent hook & background failure watcher | `src/goldseam/telemetry/hook.py`, `watcher.py` | `tests/unit/test_telemetry.py` | 4 passed tests (redaction & proposals) | PASS |
| **REQ-P12-02**| Launch materials (Show HN, blog, LinkedIn, demo script, good first issues) | `docs/launch/*.md` | Doc verification | Complete launch bundle | PASS |
| **REQ-P12-03**| Full end-to-end trace-to-skill compiler pipeline | `tests/e2e/test_e2e_compiler.py` | `tests/e2e/test_e2e_compiler.py` | Full e2e test passing | PASS |
| **REQ-P9-03** | Ablation studies harness & matrix evaluation (repair on/off, policy) | `benchmarks/ablation.py` | Comparative report in `results/` | 126 runs evaluated | PASS |
| **REQ-P11-03**| Standard SARIF v2.1.0 security & tamper export | `src/goldseam/security/sarif.py` | `tests/unit/test_sarif.py` | Validated SARIF output | PASS |
| **REQ-P11-04**| Context pruning & model cost optimizer | `src/goldseam/llm/cost_optimizer.py` | `tests/unit/test_cost_optimizer.py` | Head/tail truncation tests | PASS |
| **REQ-P12-04**| MkDocs static site & complete documentation suite | `mkdocs.yml`, `docs/*.md` | Doc verification | 14 documentation pages | PASS |
| **REQ-P12-05**| Claude Code agent plugin packaging & tools | `integrations/claude_code/` | Tool spec verification | Claude Code integration | PASS |
| **REQ-P11-05**| Library evolution manager, regression preservation & retirements | `src/goldseam/registry/evolution.py` | `tests/unit/test_evolution.py` | 2 passed tests | PASS |
| **REQ-P11-06**| Pluggable entry points & trust contracts | `src/goldseam/plugins.py` | `tests/unit/test_plugins.py` | 5 passed tests | PASS |
| **REQ-P11-07**| Multi-language JS/TS/Bash policies & runtime boundaries | `src/goldseam/security/multilang.py` | `tests/security/test_multilang.py` | 4 passed tests | PASS |
| **REQ-P3-04** | Advanced sandbox backends (bwrap, wasm, remote with cost/privacy caps) | `src/goldseam/sandbox/backends/{bwrap,wasm,remote}.py` | `tests/security/test_sandbox_backends.py` | 6 passed tests | PASS |
| **REQ-P11-08**| Terminal review dashboard & visual proposal inspectability | `src/goldseam/registry/dashboard.py` | `tests/integration/test_dashboard.py` | 2 passed tests | PASS |
| **REQ-P11-09**| Curated policy packs & reproducible build metadata | `src/goldseam/security/policy_packs.py` | `tests/unit/test_policy_packs.py` | 4 passed tests | PASS |
| **REQ-P11-10**| Human correction learning from before/after file pairs | `src/goldseam/cli.py` | `tests/integration/test_cli.py` | 13 passed tests | PASS |

