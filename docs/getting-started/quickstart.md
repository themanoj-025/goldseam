# Goldseam Quickstart Guide

This guide walks you through compiling your first failure trace into a verified skill.

## 1. Environment Verification
Verify your system environment using the built-in diagnostic tool:
```bash
goldseam doctor
```
If Docker is not running, `doctor` will report container testing as unavailable.

## 2. Ingesting a Failure Trace
Assume your agent failed to parse a messy JSON file with trailing commas and Unicode escapes:
```bash
goldseam build --from-log tests/fixtures/traces/json_unicode_fail.log --dry-run
```
This performs:
- Normalization and credential scrubbing.
- Triage: classifies the gap as `SKILL`.
- Spec Design: creates a typed `SkillSpec` with JSON Schemas.
- Independent Test Generation: generates pytest unit tests and replay oracle.
- Code Generation: writes a pure Python normalizer module and CLI wrapper.
- Static Security Analysis: scans AST for forbidden calls or dynamic imports.

## 3. Sandboxed Verification & Review
When running without `--dry-run`, Goldseam runs tests in a sandbox.
```bash
goldseam build --from-log tests/fixtures/traces/json_unicode_fail.log --target agent-skills --out ~/.goldseam/skills/
```
You will be presented with an interactive human review prompt:
- Shows the diff of generated files.
- Displays declared side-effects and imports.
- Shows sandbox test execution output.
- Options: `[A]pprove`, `[R]eject`, `[E]dit`, `[D]efer`.

## 4. Tamper Verification
Verify that an installed skill has not been modified since provenance attestation:
```bash
goldseam verify ~/.goldseam/skills/json-unicode-normalizer
```
If a single byte in `scripts/normalizer.py` has changed, verification fails with exit code 1.
