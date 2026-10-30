# Goldseam Ablation Evaluation Report

**Date:** 2026-10-25T15:23:01.225465+00:00  
**Cases Evaluated Per Run:** 42  
**Total Runtime:** 45.89s  

## Comparative Ablation Matrix

| Experiment | Repair Iterations | Policy | Triage Acc | Build Success | Hidden Oracle Pass | Security Violations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Full Pipeline)** | 3 | standard | 97.6% | 96.9% | 96.9% | 0 |
| **No Self-Repair (Repair OFF)** | 0 | standard | 97.6% | 0.0% | 0.0% | 0 |
| **Strict Security Policy** | 3 | strict | 97.6% | 96.9% | 96.9% | 0 |

### Key Findings:
- **Impact of Self-Repair:** Self-repair directly recovers first-pass compilation failures, maintaining resilient build and oracle pass rates.
- **Policy Containment:** Across all ablation runs (including standard and strict policies), zero security violations or prompt-injection attacks ever reached installation status.