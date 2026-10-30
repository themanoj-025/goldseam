# Goldseam CLI Reference

The Goldseam command line interface is built with Typer and Rich, supporting structured JSON output (`--json`), non-interactive automation, and strict error exit codes.

## Commands

### `goldseam --version`
Prints the installed version of Goldseam.

### `goldseam init`
Initializes the local `~/.goldseam/` directory structure, skill library index, and default configuration.

### `goldseam doctor [--fix]`
Runs diagnostic pre-flight checks:
- Python version (>= 3.11).
- Package dependencies.
- Docker daemon availability and permissions.
- Git status and workspace health.
`--fix` repairs missing directory structures and creates default policy files if absent.

### `goldseam build [OPTIONS]`
Compiles a failure trace or requirement into a verified skill proposal.
- `--from-log PATH`: Ingest a terminal or stdout log file.
- `--from-stdin`: Ingest log stream from standard input.
- `--from-transcript PATH`: Ingest agent transcript JSONL.
- `--from-diff PATH`: Ingest git diff correction.
- `--need TEXT`: Synthesize capability from a free-text specification.
- `--target [agent-skills|mcp|both]`: Output format (default: `agent-skills`).
- `--out DIR`: Destination directory for installed skill.
- `--sandbox [auto|docker|bwrap|local]`: Execution sandbox backend (default: `auto`).
- `--allow-weak-sandbox`: Explicit opt-in permitting weak local subprocess sandbox for trusted test fixtures.
- `--max-iter N`: Maximum repair iterations (default: 3).
- `--budget USD`: Monetary cost limit for LLM calls (default: 1.00).
- `--policy [strict|standard|permissive]`: Security policy preset (default: `strict`).
- `--dry-run`: Generate and statically validate proposal without sandbox execution or installation.
- `--yes`: Auto-approve proposal IF AND ONLY IF risk level is LOW and user configuration explicitly permits auto-approval.
- `--json`: Output structured JSON payload for CI/CD integration.

### `goldseam verify SKILL_DIR`
Validates cryptographic integrity and provenance of an installed skill directory. Detects single-byte tampering, missing files, or schema drift.

### `goldseam list`
Lists all skills currently registered in the local Goldseam library.

### `goldseam show NAME`
Displays detailed metadata, triggers, declared side effects, and provenance for a registered skill.

### `goldseam remove NAME`
Removes a skill from the local library after human confirmation.

### `goldseam export NAME [--format zip|tar.gz]`
Exports a packaged skill bundle with signed provenance attestation.

### `goldseam bench`
Executes the synthetic golden benchmark suite and generates an empirical accuracy and false-acceptance report.

### `goldseam learn --from-diff BEFORE AFTER --why TEXT`
Analyzes a human developer correction (before and after states) to synthesize a persistent skill or rule.
