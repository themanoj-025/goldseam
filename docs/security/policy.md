# Goldseam Security Policy Specifications

Goldseam enforces layered security policies before any generated code is permitted to execute in a sandbox or be installed into a user environment.

## 1. Import Allowlist Policy (`strict` vs `standard`)

### Strictly Allowed Python Standard Library Modules:
- `json`, `csv`, `re`, `math`, `datetime`, `collections`, `itertools`, `functools`
- `typing`, `dataclasses`, `enum`, `pathlib`, `hashlib`, `uuid`, `copy`
- `string`, `unicodedata`, `io`, `urllib.parse`

### Strictly Forbidden Standard Library & Built-in Modules:
- `os`, `sys` (except `sys.stdin`, `sys.stdout`, `sys.stderr`, `sys.exit`)
- `subprocess`, `shutil`, `socket`, `http.client`, `urllib.request`
- `ctypes`, `inspect`, `importlib`, `builtin`, `builtins`
- `pickle`, `shelve`, `marshal`, `tempfile` (managed by harness)
- `multiprocessing`, `threading`, `concurrent.futures`

## 2. Forbidden Python AST Patterns
- `Call` targeting `eval`, `exec`, `__import__`, `globals`, `locals`, `compile`.
- `Attribute` access matching `__class__`, `__subclasses__`, `__bases__`, `__mro__`, `__globals__`, `__code__`, `__dict__`.
- Dunder assignment (`__setattr__`, `__delattr__`).
- Dynamic string execution via `getattr` or `setattr` on module objects.

## 3. Sandboxing Invariants
- Non-root user inside container (`uid: 10001, gid: 10001`).
- Root filesystem is mounted read-only (`--read-only`).
- No external network access (`--network none`).
- Capability drop: all Linux capabilities dropped (`--cap-drop ALL`).
- Security flag: `--security-opt no-new-privileges`.
- Hard resource bounds: 512MB RAM, 1 CPU core, max 64 PIDs, 30s wall-clock timeout.
- Host bind mounts strictly prohibited except for an isolated, sanitized staging directory created in a temporary location.
