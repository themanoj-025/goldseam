"""Multi-language validation policies and security boundaries (JS, TS, Bash, Python).

Invariant: Python AST allowlisting must NEVER be represented as protecting non-Python code.
Each language requires language-specific static policies and independent container sandbox environments.
"""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from goldseam.errors import SecurityPolicyError


class SupportedLanguage(StrEnum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    UNKNOWN = "unknown"


class LanguageSecurityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    language: SupportedLanguage
    passed: bool
    violations: list[str] = Field(default_factory=list)
    requires_isolated_runtime: str = Field(description="Designated sandbox environment")


class MultiLanguagePolicyValidator:
    """Enforces language-specific security policies and sandboxing boundaries."""

    # Disallowed dangerous JS/TS patterns
    DANGEROUS_JS_PATTERNS = [
        (re.compile(r"\beval\s*\("), "Dynamic execution via eval() is forbidden"),
        (re.compile(r"\bFunction\s*\("), "Dynamic execution via Function constructor is forbidden"),
        (re.compile(r"(?:require\s*\(\s*['\"]child_process['\"]|from\s+['\"]child_process['\"])"), "child_process execution is forbidden"),
        (re.compile(r"(?:require\s*\(\s*['\"]net['\"]|from\s+['\"]net['\"])"), "Ambient networking via 'net' module is forbidden"),
        (re.compile(r"(?:require\s*\(\s*['\"]dgram['\"]|from\s+['\"]dgram['\"])"), "Datagram sockets via 'dgram' module is forbidden"),
        (re.compile(r"(?:require\s*\(\s*['\"]cluster['\"]|from\s+['\"]cluster['\"])"), "Process clustering is forbidden"),
        (re.compile(r"\bprocess\.exit\s*\("), "Abrupt process termination via process.exit() is forbidden"),
    ]

    # Disallowed dangerous Bash patterns
    DANGEROUS_BASH_PATTERNS = [
        (re.compile(r"\brm\s+-[rR]*f\s+/\b"), "Dangerous recursive root deletion"),
        (re.compile(r"(?i)\b(?:curl|wget|nc|ncat|netcat)\b"), "Ambient network calls forbidden in scripts"),
        (re.compile(r"/dev/(?:tcp|udp)/"), "Direct network socket manipulation via /dev/(tcp|udp)"),
        (re.compile(r"\b(?:sudo|su|doas)\b"), "Privilege escalation attempts forbidden"),
        (re.compile(r"\bmkfs\b"), "Filesystem formatting forbidden"),
        (re.compile(r"\bchmod\s+[0-7]?[421][0-7]{2}\b"), "Setting SUID/SGID executable bits forbidden"),
    ]

    @classmethod
    def detect_language(cls, file_path: str) -> SupportedLanguage:
        path_lower = file_path.lower()
        if path_lower.endswith(".py"):
            return SupportedLanguage.PYTHON
        elif path_lower.endswith(".ts"):
            return SupportedLanguage.TYPESCRIPT
        elif path_lower.endswith(".js") or path_lower.endswith(".mjs"):
            return SupportedLanguage.JAVASCRIPT
        elif path_lower.endswith(".sh") or path_lower.endswith(".bash"):
            return SupportedLanguage.BASH
        return SupportedLanguage.UNKNOWN

    @classmethod
    def validate_code(cls, file_path: str, content: str) -> LanguageSecurityResult:
        lang = cls.detect_language(file_path)

        if lang == SupportedLanguage.UNKNOWN:
            return LanguageSecurityResult(
                language=lang,
                passed=False,
                violations=[f"Unsupported language file extension for '{file_path}'. Fails closed."],
                requires_isolated_runtime="unsupported",
            )

        if lang == SupportedLanguage.PYTHON:
            # Python validation is handled by AstVisitor & ImportPolicy
            return LanguageSecurityResult(
                language=lang,
                passed=True,
                violations=[],
                requires_isolated_runtime="python:3.12-slim",
            )

        violations: list[str] = []

        if lang in (SupportedLanguage.TYPESCRIPT, SupportedLanguage.JAVASCRIPT):
            for pattern, reason in cls.DANGEROUS_JS_PATTERNS:
                if pattern.search(content):
                    violations.append(reason)
            return LanguageSecurityResult(
                language=lang,
                passed=len(violations) == 0,
                violations=violations,
                requires_isolated_runtime="node:20-alpine-isolated",
            )

        if lang == SupportedLanguage.BASH:
            # Check for safety preamble
            if "set -euo pipefail" not in content and "set -e" not in content:
                violations.append("Bash scripts must include strict error handling ('set -euo pipefail')")

            for pattern, reason in cls.DANGEROUS_BASH_PATTERNS:
                if pattern.search(content):
                    violations.append(reason)

            return LanguageSecurityResult(
                language=lang,
                passed=len(violations) == 0,
                violations=violations,
                requires_isolated_runtime="alpine:3.20-isolated",
            )

        raise SecurityPolicyError(f"Unhandled language: {lang}")
