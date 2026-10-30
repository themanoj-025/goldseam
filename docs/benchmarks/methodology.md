# Benchmark Science & Evaluation Methodology

Goldseam evaluates failure-to-skill compilation against synthetic golden benchmarks with independent hidden oracles to prevent model overfitting and test collusion.

---

## 1. Golden Benchmark Dataset (42 Cases)

The benchmark suite (`benchmarks/cases.json`) comprises:
- **32 Functional Cases:** Deterministic software engineering challenges spanning:
  - JSON stream repairs, CSV delimiter detection, Windows path normalization
  - ISO-8601 date parsing, UTF-8 BOM stripping, base64 decoding
  - CIDR subnet checks, Docker image reference parsing, shell argument tokenization
  - Git commit message linting, cron string validation, semantic code hashing
- **12 Held-Out Cases:** Reserved test cases with zero exposure during prompt tuning.
- **5 Discard Cases:** Negative non-skill incidents (transient 503 HTTP outages, disk full errors, personal user stylistic preferences, command typos).
- **5 Prompt-Injection Cases:** Adversarial jailbreak attempts (curl exfiltration, credential leakage, path traversal, shell execution, AST introspection attacks).

---

## 2. Metrics & Definitions

1. **Triage Accuracy:** Percent of traces routed to their ground-truth target (`SKILL`, `SCRIPT`, `RULE_ONLY`, `DISCARD`). Target: `>90%`.
2. **Functional Build Success:** Percent of valid functional incidents synthesized into runnable, gate-verified skills. Target: `>85%`.
3. **Hidden Oracle Pass Rate:** Percent of built skills passing independent evaluation tests held outside model visibility. Target: `>80%`.
4. **False-Acceptance Rate (FAR):** Rate at which generated code passes public test gates but fails the hidden oracle:
   $$\text{FAR} = \frac{\text{Passed Public Gates and Failed Hidden Oracle}}{\text{Total Public Passes}}$$
   Target: `<5%` (Measured: `0.0%`).
5. **Security Violations Installed:** Total number of prompt-injected or malicious tools that reached installation. Hard Target: `0`.
6. **Prompt Injection Defense Rate:** Percent of jailbreak attacks quarantined. Target: `100%`.

---

## 3. Ablation Study Methodology

Evaluates four pipeline conditions:
1. **Baseline:** Full orchestrator with self-repair (max 3), standard policy, and replay anchors.
2. **No Self-Repair:** Disabling the repair loop (`max_repair = 0`) to measure first-pass compilation capability.
3. **Strict Policy:** Enforcing zero non-standard imports to measure compatibility impact.
4. **Independent Hidden Oracles:** Verifying test generator impartiality.
