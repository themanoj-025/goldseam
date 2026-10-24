# Contributing to Goldseam

Thank you for contributing to Goldseam! We welcome contributions that improve safety, accuracy, and performance.

## Development Workflow

1. **Prerequisites:**
   - Python 3.11 or 3.12
   - `uv` package manager (`https://docs.astral.sh/uv/`)
   - Docker daemon (for hardened sandbox verification)

2. **Setup:**
   ```bash
   uv sync --extra dev --extra llm
   ```

3. **Code Style & Quality:**
   - Code must pass `ruff check .` and `ruff format --check .`
   - Strict typing with `mypy src` must report zero errors.
   - All tests must pass with `uv run pytest`.
   - Security regression tests in `tests/security/` must never be weakened or deleted.

4. **Pull Requests:**
   - Open PRs against `main`.
   - Ensure `docs/IMPLEMENTATION_MATRIX.md` is updated if adding or modifying features.
