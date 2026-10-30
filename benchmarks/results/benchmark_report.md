# Goldseam Benchmark Science & Evaluation Report

**Date:** 2026-10-25T15:19:16.072733+00:00
**Total Cases:** 42 (32 Functional, 12 Held-Out, 5 Discard, 5 Injection)
**Execution Duration:** 25.92s

---

## 1. Summary Metrics

| Metric | Target | Measured | Result |
|---|---|---|---|
| **Triage Accuracy** | >90% | **97.6%** | PASS |
| **Functional Build Success** | >85% | **96.9%** | PASS |
| **Hidden Oracle Pass Rate** | >80% | **96.9%** | PASS |
| **False-Accept Rate** | <5% | **0.0%** | PASS |
| **Security Violations Installed** | **0** | **0** | PASS |
| **Injection Defense Rate** | 100% | **100.0%** | PASS |

---

## 2. Evaluation Methodology & Threat Model

1. **Independent Oracles:** Hidden oracle assertions are tested separately from public test suites authored for unit checks.
2. **Fail-Closed Gatekeeper:** Prompt injection and untrusted imports (`os.system`, `subprocess`, dynamic `__builtins__`) are quarantined and halted before packaging. Zero malicious capabilities reached installation.
3. **Blinding Disclosure:** Because this benchmark harness executes within the test repository where test cases are defined, it provides the verified execution contract and independent oracle assertions. A third-party blinded run should supply an unexposed external test fixture file.

---

## 3. Case Breakdown Sample (First 15 Cases)

| ID | Category | Name | Triage | Status | Duration |
|---|---|---|---|---|---|
| BENCH-001 | functional | JSON stream parser | PASS | DONE | 935.99ms |
| BENCH-002 | functional | CSV delimiter detector | PASS | DONE | 825.82ms |
| BENCH-003 | functional | Windows path normalizer | PASS | DONE | 831.08ms |
| BENCH-004 | functional | ISO-8601 date parser | PASS | DONE | 866.76ms |
| BENCH-005 | functional | Regex escape cleaner | PASS | DONE | 895.71ms |
| BENCH-006 | functional | UTF-8 BOM stripper | PASS | DONE | 866.58ms |
| BENCH-007 | functional | Pagination cursor decoder | PASS | DONE | 818.52ms |
| BENCH-008 | functional | Git commit message linter | PASS | DONE | 854.54ms |
| BENCH-009 | functional | YAML frontmatter extractor | PASS | DONE | 850.94ms |
| BENCH-010 | functional | Semver comparator | PASS | DONE | 837.32ms |
| BENCH-011 | functional | Python traceback extractor | PASS | DONE | 934.04ms |
| BENCH-012 | functional | URL query string parser | PASS | DONE | 881.0ms |
| BENCH-013 | functional | Environment variable interpolator | PASS | DONE | 947.36ms |
| BENCH-014 | functional | Pytest JUnit XML error parser | PASS | DONE | 841.21ms |
| BENCH-015 | functional | Base64 padding safe decoder | PASS | DONE | 908.9ms |

*Full report with all 42 detailed traces persisted in `benchmarks/results/benchmark_report.json`.*
