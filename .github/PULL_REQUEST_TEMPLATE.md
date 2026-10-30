## Description
<!-- Provide a brief summary of the change and motivation -->

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing behavior to change)
- [ ] Documentation update
- [ ] Performance or security hardening

## Security & Engineering Invariants Verification
- [ ] Invariant 1: Untrusted generated code remains isolated from host runtime
- [ ] Invariant 2: Execution traces and error logs are sanitized of secrets and PII
- [ ] Invariant 3: Sandbox operates fail-closed with verified container isolation
- [ ] Invariant 4: Replay oracles and anchor tests are cryptographically immutable
- [ ] Invariant 7: Test suites pass offline without external network or live LLM keys
- [ ] Invariant 9: Static type checking passes strictly with zero errors (`mypy src`)

## Testing & Verification
<!-- Describe the tests executed and output observed -->
```bash
uv run ruff check .
uv run mypy src
uv run pytest
```
