"""Unified static security validator for generated bundles."""

import time

from goldseam.models.bundle import GeneratedBundle
from goldseam.models.result import GateOutcome, GateResult
from goldseam.security.ast_visitor import analyze_python_code
from goldseam.security.import_policy import SecurityPolicy
from goldseam.security.secrets_scan import scan_for_secrets
from goldseam.security.skillmd_lint import lint_skill_md


class StaticSecurityValidator:
    def __init__(self, policy: SecurityPolicy | None = None, preset: str = "strict") -> None:
        self.policy = policy or SecurityPolicy.load_default()
        self.preset = preset

    def validate_bundle(self, bundle: GeneratedBundle) -> list[GateResult]:
        """Runs all static policy gates on a generated bundle."""
        results: list[GateResult] = []

        # Gate 1: SKILL.md Lint
        start_t = time.perf_counter()
        skill_file = bundle.get_file("SKILL.md")
        if not skill_file:
            results.append(
                GateResult(
                    gate="skillmd_lint",
                    passed=False,
                    outcome=GateOutcome.POLICY,
                    evidence="Missing required SKILL.md file in bundle",
                    duration_ms=(time.perf_counter() - start_t) * 1000,
                )
            )
        else:
            violations = lint_skill_md(skill_file.content, expected_slug=bundle.skill_slug)
            passed = len(violations) == 0
            results.append(
                GateResult(
                    gate="skillmd_lint",
                    passed=passed,
                    outcome=GateOutcome.PASS if passed else GateOutcome.POLICY,
                    evidence="; ".join(violations) if violations else "SKILL.md strictly conformant",
                    duration_ms=(time.perf_counter() - start_t) * 1000,
                )
            )

        # Gate 2: AST Security Analysis on generated tool scripts
        start_t = time.perf_counter()
        ast_errors: list[str] = []
        for f in bundle.files:
            if f.path.startswith("scripts/") and f.path.endswith(".py"):
                findings, _ = analyze_python_code(f.content, self.policy, self.preset)
                for finding in findings:
                    ast_errors.append(
                        f"[{f.path}:{finding.line}] {finding.rule}: {finding.message}"
                    )
        ast_passed = len(ast_errors) == 0
        results.append(
            GateResult(
                gate="ast_security",
                passed=ast_passed,
                outcome=GateOutcome.PASS if ast_passed else GateOutcome.POLICY,
                evidence="; ".join(ast_errors) if ast_errors else "All Python scripts passed AST policy",
                duration_ms=(time.perf_counter() - start_t) * 1000,
            )
        )

        # Gate 3: Secrets Scanner
        start_t = time.perf_counter()
        secret_findings: list[str] = []
        for f in bundle.files:
            sec_findings = scan_for_secrets(f.content)
            for sf in sec_findings:
                secret_findings.append(
                    f"[{f.path}:{sf.line}] {sf.rule} detected (preview: {sf.preview})"
                )
        secrets_passed = len(secret_findings) == 0
        results.append(
            GateResult(
                gate="secrets_scan",
                passed=secrets_passed,
                outcome=GateOutcome.PASS if secrets_passed else GateOutcome.POLICY,
                evidence="; ".join(secret_findings) if secret_findings else "No credentials or high-entropy secrets found",
                duration_ms=(time.perf_counter() - start_t) * 1000,
            )
        )

        return results
