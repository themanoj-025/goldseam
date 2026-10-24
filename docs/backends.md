# Sandbox Execution Backends

Untrusted generated code must never execute within the host developer environment. Goldseam implements isolated sandbox runners adhering to strict fail-closed security invariants.

---

## 1. Supported Backends

### 1. Hardened Docker Sandbox (`DockerSandboxRunner`) — Default
The primary security boundary for testing generated tools.
- **Network Isolation:** `--network none` (strictly no outbound or inbound connections).
- **Filesystem Security:** `--read-only` root filesystem; disposable tmpfs for `/tmp`.
- **Least Privilege:** Dropped all Linux capabilities (`--cap-drop ALL`), `--security-opt no-new-privileges`, non-root user (`uid 10001`).
- **Resource Limits:** Hard-capped memory (512MB default), CPU quotas (1 core), process count (pids-limit 64), and execution timeout (30s default).
- **Fail-Closed Behavior:** If the Docker daemon is offline or unreachable, installation status immediately reports `BLOCKED` to prevent accidental unhardened execution.

### 2. Bubblewrap Backend (`BubblewrapSandboxRunner`)
Available on Linux hosts with unprivileged user namespaces (`bwrap`):
- Creates disposable read-only bind mounts (`/usr`, `/lib`, `/bin`).
- Unshares IPC, PID, network, and UTS namespaces.
- Enforces memory quotas and wall-clock execution deadlines.

### 3. Local Subprocess Runner (`LocalSandboxRunner`) — Opt-In Only
- Intended strictly for trusted internal unit test fixtures in environments lacking Docker.
- **Fail-Closed Gate:** Refuses to run unless `--allow-weak-sandbox` is explicitly supplied by the user.
- **Warning:** Never safe for untrusted, model-generated code in untrusted workspaces.
