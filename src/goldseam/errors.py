"""Goldseam typed exception hierarchy."""


class GoldseamError(Exception):
    """Base exception for all Goldseam errors."""


class IngestError(GoldseamError):
    """Raised when parsing or normalizing an input trace fails."""


class RedactionError(GoldseamError):
    """Raised when redaction fails or encounters an irrecoverable pattern."""


class TriageError(GoldseamError):
    """Raised when trace classification or capability triage fails."""


class RoutingError(GoldseamError):
    """Raised when routing to a target output class fails."""


class SpecError(GoldseamError):
    """Raised when synthesizing or validating a SkillSpec fails."""


class GenerationError(GoldseamError):
    """Raised when code or bundle synthesis fails."""


class TestGenError(GoldseamError):
    """Raised when generating tests or replay oracles fails."""


class SecurityPolicyError(GoldseamError):
    """Base class for static security and policy gate failures."""


class ASTViolationError(SecurityPolicyError):
    """Raised when code AST contains disallowed imports, calls, or attributes."""


class SecretLeakError(SecurityPolicyError):
    """Raised when potential credentials or secrets are detected in output artifacts."""


class SkillMdLintError(SecurityPolicyError):
    """Raised when SKILL.md violates the official Agent Skills specification."""


class SandboxError(GoldseamError):
    """Base exception for sandbox execution failures."""


class SandboxBlockedError(SandboxError):
    """Raised when required container sandbox isolation is unavailable (fail-closed)."""


class SandboxTimeoutError(SandboxError):
    """Raised when a sandbox execution exceeds its hard timeout limit."""


class SandboxOOMError(SandboxError):
    """Raised when a sandbox execution is terminated due to out-of-memory limits."""


class RepairExhaustedError(GoldseamError):
    """Raised when self-repair iterations or budget are exhausted without passing gates."""


class OscillationError(GoldseamError):
    """Raised when the repair engine detects alternating repeating failure signatures."""


class BudgetExceededError(GoldseamError):
    """Raised when LLM call cost or token consumption exceeds configured thresholds."""


class LLMProviderError(GoldseamError):
    """Raised when an external or local LLM provider fails."""


class PackagingError(GoldseamError):
    """Raised when assembling, atomic staging, or packaging a skill bundle fails."""


class ProvenanceTamperError(GoldseamError):
    """Raised when artifact hashes fail verification against provenance attestation."""


class ReviewRejectedError(GoldseamError):
    """Raised when a human reviewer rejects or defers a generated skill proposal."""
