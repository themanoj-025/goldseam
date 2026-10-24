# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-24
### Added
- Core failure-to-skill compiler pipeline architecture.
- Pydantic v2 data contracts for traces, specs, bundles, gates, and provenance.
- Ingestion adapters for terminal logs, pytest logs, tracebacks, diffs, and plain text.
- High-entropy credential and PII redactor.
- Capability triage and routing engine (SKILL, SCRIPT, MCP_TOOL, RULE_ONLY, DISCARD).
- Pinned Agent Skills specification parser, renderer, and linter.
- Hardened sandbox execution engine with Docker and isolated subprocess runners.
- LLM provider adapters for OpenAI, Anthropic, Ollama, and deterministic FakeLLM.
- Independent test generation and bounded self-repair engine.
- Provenance tracking, SHA-256 tamper detection, and atomic packaging.
- Typer/Rich CLI interface and standalone MCP stdio server emitter.
