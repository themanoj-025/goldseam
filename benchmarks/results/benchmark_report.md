# Goldseam Benchmark Science & Evaluation Report

**Date:** 2026-10-24T18:38:23.868368+00:00
**Total Cases:** 42 (32 Functional, 12 Held-Out, 5 Discard, 5 Injection)
**Execution Duration:** 27.91s

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
| BENCH-001 | functional | JSON stream parser | PASS | DONE | 801.67ms |
| BENCH-002 | functional | CSV delimiter detector | PASS | DONE | 791.45ms |
| BENCH-003 | functional | Windows path normalizer | PASS | DONE | 763.79ms |
| BENCH-004 | functional | ISO-8601 date parser | PASS | DONE | 768.79ms |
| BENCH-005 | functional | Regex escape cleaner | PASS | DONE | 754.07ms |
| BENCH-006 | functional | UTF-8 BOM stripper | PASS | DONE | 743.92ms |
| BENCH-007 | functional | Pagination cursor decoder | PASS | DONE | 824.98ms |
| BENCH-008 | functional | Git commit message linter | PASS | DONE | 843.35ms |
| BENCH-009 | functional | YAML frontmatter extractor | PASS | DONE | 787.75ms |
| BENCH-010 | functional | Semver comparator | PASS | DONE | 818.06ms |
| BENCH-011 | functional | Python traceback extractor | PASS | DONE | 896.48ms |
| BENCH-012 | functional | URL query string parser | PASS | DONE | 870.52ms |
| BENCH-013 | functional | Environment variable interpolator | PASS | DONE | 855.58ms |
| BENCH-014 | functional | Pytest JUnit XML error parser | PASS | DONE | 877.6ms |
| BENCH-015 | functional | Base64 padding safe decoder | PASS | DONE | 840.44ms |

*Full report with all 42 detailed traces persisted in `benchmarks/results/benchmark_report.json`.*
