"""Privacy-preserving redaction engine for traces, credentials, and prompt injections."""

import re

# Deterministic pattern matchers for redaction
REDACTION_RULES = [
    ("API_KEY", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("GITHUB_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA)?\s*PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA|OPENSSH|EC|DSA)?\s*PRIVATE\s+KEY-----")),
    ("BEARER_TOKEN", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}")),
    ("EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("IPV4", re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")),
    ("USER_PATH_WIN", re.compile(r"(?i)[a-z]:\\users\\[a-z0-9_\-\.]+", re.IGNORECASE)),
    ("USER_PATH_NIX", re.compile(r"/home/[a-z0-9_\-\.]+")),
]

# Patterns indicating prompt injection or system override attempts in logs
INJECTION_PATTERNS = [
    ("ROLE_SPOOF", re.compile(r"(?i)(?:system:|assistant:|user:|<\|im_start\|>|<\|im_end\|>)")),
    ("INSTRUCTION_OVERRIDE", re.compile(r"(?i)(?:ignore\s+previous\s+instructions|disregard\s+all\s+rules|override\s+policy|new\s+system\s+prompt|reveal\s+all\s+(?:api\s+keys|secrets))")),
    ("EXFILTRATION_CALL", re.compile(r"(?i)(?:send\s+all\s+secrets|curl\s+https?://|wget\s+https?://|exfiltrate|os\.system|subprocess|__builtins__|socket)")),
    ("PATH_TRAVERSAL_INJECTION", re.compile(r"(?i)(?:\.\.[/\\]|[/\\]etc[/\\]|backdoor)")),
    ("MARKDOWN_TAG_INJECTION", re.compile(r"</?(?:script|iframe|style|object)>")),
]


class Redactor:
    def __init__(self) -> None:
        self.placeholder_cache: dict[str, str] = {}
        self.type_counters: dict[str, int] = {}

    def _get_placeholder(self, token_type: str, raw_value: str) -> str:
        cache_key = f"{token_type}:{raw_value}"
        if cache_key in self.placeholder_cache:
            return self.placeholder_cache[cache_key]

        count = self.type_counters.get(token_type, 0) + 1
        self.type_counters[token_type] = count
        placeholder = f"[REDACTED_{token_type}_{count}]"
        self.placeholder_cache[cache_key] = placeholder
        return placeholder

    def redact(self, text: str) -> tuple[str, dict[str, int], list[str]]:
        """
        Redacts credentials, IPs, paths, and PII.
        Returns (redacted_text, redaction_counts, injection_flags).
        """
        clean_text = text
        counts: dict[str, int] = {}
        flags: list[str] = []

        # 1. Detect prompt injection indicators
        for flag_name, pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                flags.append(flag_name)

        # 2. Redact secrets with typed placeholders
        for token_type, pattern in REDACTION_RULES:
            matches = list(pattern.finditer(clean_text))
            if matches:
                counts[token_type] = len(matches)
                # Replace in reverse to preserve string indices
                for m in reversed(matches):
                    raw_val = m.group(0)
                    placeholder = self._get_placeholder(token_type, raw_val)
                    clean_text = clean_text[:m.start()] + placeholder + clean_text[m.end():]

        return clean_text, counts, flags
