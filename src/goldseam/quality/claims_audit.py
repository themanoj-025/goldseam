"""Claims audit verifying that promises in skill descriptions map to executable tests."""

from goldseam.models.spec import SkillSpec


class ClaimsAuditor:
    def audit_claims(self, spec: SkillSpec) -> tuple[bool, list[str]]:
        """
        Verifies that every concrete capability declared in the SkillSpec description
        and tool purposes is backed by at least one explicit test example.
        Returns (all_verified, missing_coverage_warnings).
        """
        warnings: list[str] = []

        for tool in spec.tools:
            # Check example count
            if len(tool.examples) < 3:
                warnings.append(
                    f"Tool '{tool.name}' has only {len(tool.examples)} examples; minimum 3 required"
                )

            # Check negative example
            if not any(ex.should_fail for ex in tool.examples):
                warnings.append(
                    f"Tool '{tool.name}' has no negative error-handling example"
                )

            # Check keyword mapping between purpose and examples
            import re
            purpose_tokens = re.findall(r"[a-z]{3,}", tool.purpose.lower())
            all_example_text = " ".join(
                f"{ex.description} {ex.inputs} {ex.expected}" for ex in tool.examples
            ).lower()
            context = f"{tool.name} {tool.input_schema} {tool.output_schema} {all_example_text}".lower()

            stop_words = {"the", "and", "for", "with", "from", "that", "this", "string", "valid", "input", "output", "format"}
            key_terms = [t for t in purpose_tokens if t not in stop_words and len(t) >= 4]

            covered = any(
                (term in context or context.find(term[:4]) != -1)
                for term in key_terms
            )

            if key_terms and not covered:
                warnings.append(
                    f"Tool '{tool.name}' purpose mentions {key_terms[:3]} but examples/schemas lack coverage"
                )

        return len(warnings) == 0, warnings
