# Security Policy

## Core Invariants
Goldseam is built around strict security controls:
1. **Never Trust Generated Code:** Generated code and tests are treated as potentially adversarial and are never executed in the host interpreter process.
2. **Sandbox Isolation:** All evaluation and execution runs in an isolated, capability-dropped, unprivileged, non-networked Docker container (or explicit opt-in weak subprocess runner only for trusted dev fixtures).
3. **No Dynamic Execution on Host:** `eval()`, `exec()`, `__import__()`, or dynamic attribute access from untrusted inputs are blocked.
4. **Redaction Prior to External Dispatch:** Secrets, credentials, tokens, paths, and user identities are scrubbed before any external LLM invocation.
5. **Human Authorization Required:** Installation of skills into active agent repositories requires human confirmation.

## Reporting a Vulnerability
If you discover a security vulnerability in Goldseam (e.g. sandbox breakout, parser confusion, redaction bypass, or privilege escalation):
1. **Do NOT open a public GitHub issue.**
2. Send an email with reproduction steps and an adversarial trace to `security@goldseam.local` (or file a private GitHub Advisory).
3. We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure plan.
