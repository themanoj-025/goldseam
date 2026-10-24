"""High-entropy secret scanner and pattern-based credential detector."""

import math
import re

from pydantic import BaseModel, ConfigDict

SECRET_PATTERNS = [
    ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("GITHUB_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA)?\s*PRIVATE\s+KEY-----")),
    ("GENERIC_BEARER", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}")),
    ("GENERIC_SECRET_KV", re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*[:=]\s*["']?([a-zA-Z0-9_\-\.]{16,})["']?""")),
]


class SecretFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule: str
    line: int
    preview: str


def calculate_shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    counts: dict[str, int] = {}
    for char in data:
        counts[char] = counts.get(char, 0) + 1
    for count in counts.values():
        p_x = count / length
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


def scan_for_secrets(text: str, entropy_threshold: float = 4.2) -> list[SecretFinding]:
    """Scans text for credential patterns and suspicious high-entropy tokens."""
    findings: list[SecretFinding] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        # 1. Regex pattern matching
        for rule_name, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                raw_match = match.group(0)
                preview = raw_match[:4] + "..." + raw_match[-4:] if len(raw_match) > 8 else "***"
                findings.append(SecretFinding(rule=rule_name, line=idx, preview=preview))

        # 2. Entropy token scanning on long word tokens
        words = re.findall(r"[a-zA-Z0-9_\-+/=]{24,}", line)
        for word in words:
            # Skip common false positives (e.g. long repetitive characters, urls)
            if word.startswith("http") or len(set(word)) < 5:
                continue
            entropy = calculate_shannon_entropy(word)
            if entropy >= entropy_threshold:
                preview = word[:4] + "..." + word[-4:]
                findings.append(
                    SecretFinding(rule="HIGH_ENTROPY_TOKEN", line=idx, preview=preview)
                )

    return findings
