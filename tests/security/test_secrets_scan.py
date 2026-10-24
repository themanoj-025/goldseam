"""Tests for high-entropy secrets and credential scanner."""

from goldseam.security.secrets_scan import scan_for_secrets


def test_clean_text_no_secrets() -> None:
    text = "def calculate_sum(a: int, b: int) -> int:\n    return a + b"
    findings = scan_for_secrets(text)
    assert len(findings) == 0


def test_detect_openai_api_key() -> None:
    text = 'client = OpenAI(api_key="sk-abcdefghijklmnopqrstuvwxyz1234567890")'
    findings = scan_for_secrets(text)
    assert len(findings) > 0
    assert any(f.rule == "OPENAI_KEY" for f in findings)


def test_detect_github_token() -> None:
    text = "Authorization: token ghp_123456789012345678901234567890123456"
    findings = scan_for_secrets(text)
    assert len(findings) > 0
    assert any(f.rule == "GITHUB_TOKEN" for f in findings)


def test_detect_private_key() -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
    findings = scan_for_secrets(text)
    assert len(findings) > 0
    assert any(f.rule == "PRIVATE_KEY" for f in findings)


def test_detect_high_entropy_token() -> None:
    # Random base64 string
    text = 'secret_blob = "QXZkZlR5dWlvcGFTZGZnaGprbHpYY3Zibm0xMjM0NTY="'
    findings = scan_for_secrets(text)
    assert len(findings) > 0
    assert any(f.rule == "HIGH_ENTROPY_TOKEN" for f in findings)
