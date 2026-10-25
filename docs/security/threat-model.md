# Goldseam Threat Model & Security Boundaries

## 1. Threat Profile
Goldseam operates directly on untrusted inputs: raw system logs, agent failure traces, LLM prompt responses, and newly generated executable Python code.

### Untrusted Assets:
- Raw terminal logs and error dumps (may contain credentials, PII, prompt injections).
- LLM outputs (code, markdown, tests, self-declared risk ratings).
- Generated Python scripts and third-party import dependencies.

### Trusted Components:
- The Goldseam host orchestrator and CLI.
- AST allowlist analyzer and security policy rules (`policy.toml`).
- Sanitized replay oracle anchors.
- Hardened container sandbox harness.
- Cryptographic hashing and provenance engine.

---

## 2. Threat Matrix & Defense Strategy

| Threat | Attack Vector | Goldseam Defense |
| :--- | :--- | :--- |
| **Prompt Injection** | Log trace contains instructions to ignore constraints, exfiltrate data, or write malicious tools | Parser treats traces strictly as inert data; redaction strips command tokens; output strictly validated via Pydantic schemas |
| **Arbitrary Code Execution on Host** | Generated tool attempts `os.system()`, `subprocess.Popen()`, or socket connections on developer machine | Untrusted code is never imported or executed in the host process. Execution is confined to a container sandbox |
| **Sandbox Escape** | Vulnerability in runtime or container mount escapes to host filesystem | Container configured with `--network none`, `--read-only`, non-root user, `--cap-drop ALL`, `--security-opt no-new-privileges`, memory/CPU quotas, and sanitized disposable bind-mount |
| **AST Filter Evasion** | Dynamic obfuscation (`getattr(__builtins__, "eval")`, `base64.b64decode`, string concatenation) | AST is an early-rejection heuristic only. Container isolation provides true containment. Dynamic attributes and eval are strictly rejected |
| **Credential Exfiltration** | Traces contain live API keys or cloud tokens transmitted to LLM | Regex and entropy scanner redacts secrets before model dispatch. Dry-run mode stores only cryptographic hashes |
| **Test Tampering / Cheating** | Repair LLM edits unit tests or weakens assertions to make bad code pass | Test suites and replay oracles are authored independently and locked via immutable SHA-256 hashes. Repair engine cannot touch test files |
| **Path Traversal / Host Overwrite** | Generated bundle writes to `../../.bashrc` or Windows system files | Bundle packager validates all file targets, rejecting relative jumps (`..`), absolute paths, and Windows reserved names (`CON`, `PRN`, `NUL`) |
| **Provenance Tampering** | Adversary alters installed skill code post-verification | `goldseam verify` recalculates SHA-256 tree against `provenance.json` and flags single-byte discrepancies |
