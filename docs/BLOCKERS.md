# Goldseam Blockers and Diagnostic Findings

## Active Blockers

### BLK-01: Host Docker Daemon Offline
- **Severity:** HIGH (Mitigated by Architecture)
- **Component:** `src/goldseam/sandbox/backends/docker.py`
- **Observed Behavior:** Query to Docker engine via `docker ps` fails with:
  `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
  Windows service `com.docker.service` is in `Stopped` state.
- **Root Cause:** Docker Desktop application is not actively running on the host Windows machine.
- **Security Impact:** In accordance with **Invariant 3 (Sandbox Fail-Closed)**, untrusted generated code must not be executed without verification in a container sandbox. Any command attempting to install unverified code without an active container sandbox will return status `BLOCKED`.
- **Workaround / Development Mitigation:** A lightweight local subprocess runner is available under `src/goldseam/sandbox/backends/local.py` solely when the explicit flag `--allow-weak-sandbox` is provided for trusted internal fixtures and test suites. This backend is explicitly marked `WEAK` and never reported as secure.
- **Resolution Path:** Starting Docker Desktop provides live container testing.

---

## Resolved / Non-blocking Diagnostic Notes
- **Python Version:** Multiple python versions detected; uv pinned CPython 3.12.13 in isolated `.venv`.
- **OS Platform:** Windows 10/11 x64. Path sanitization logic explicitly handles Windows reserved filenames (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) and path separators (`\` vs `/`).
