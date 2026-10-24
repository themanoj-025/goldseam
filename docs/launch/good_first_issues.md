# Good First Issues for New Contributors

Welcome to Goldseam! Here are beginner-friendly and intermediate tasks ready for community contributors:

---

### Issue 1: Add a Log Ingest Adapter for GitHub Actions Workflow Logs
- **Difficulty:** Good First Issue
- **Area:** `src/goldseam/ingest/`
- **Description:** Implement a `GitHubActionsLogAdapter` that parses ANSI timestamps and step failure markers from exported GitHub Actions job logs (`.log` or `.txt`).

---

### Issue 2: Expand Regex Redaction Rules for GCP and Azure Service Tokens
- **Difficulty:** Good First Issue
- **Area:** `src/goldseam/ingest/redact.py`
- **Description:** Add regex patterns for Google Cloud Service Account private keys (`private_key_id`) and Azure Storage SAS tokens to ensure they are replaced with typed placeholders.

---

### Issue 3: Implement WebAssembly (WASM) Sandbox Backend Prototype
- **Difficulty:** Intermediate
- **Area:** `src/goldseam/sandbox/backends/`
- **Description:** Implement a lightweight `WasmSandboxRunner` utilizing `wasmtime` or `wasmer` for executing pure Python deterministic modules compiled to WASM.

---

### Issue 4: Rich Interactive Terminal Dashboard for `goldseam review`
- **Difficulty:** Intermediate
- **Area:** `src/goldseam/cli.py`
- **Description:** Enhance `goldseam review` with interactive keybindings (Approve, Edit, Reject, Diff View) using Rich's Live Layout or Textual.
