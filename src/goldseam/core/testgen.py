"""Independent test generator synthesizing pytest suites strictly from SkillSpec contracts."""

import hashlib
import json

from goldseam.models.bundle import GeneratedFile
from goldseam.models.spec import SkillSpec, ToolSpec


def generate_tool_tests(tool: ToolSpec) -> str:
    """Derives independent pytest suite from ToolSpec examples and schemas."""
    lines: list[str] = [
        f'"""Auto-generated pytest regression suite for {tool.name}."""',
        "",
        "import pytest",
        f"from scripts.{tool.name} import {tool.name}",
        "",
    ]

    for idx, ex in enumerate(tool.examples, start=1):
        test_fn_name = f"test_{tool.name}_case_{idx}"
        kwargs_repr = json.dumps(ex.inputs)

        if ex.should_fail:
            lines.extend([
                f"def {test_fn_name}() -> None:",
                f'    """{ex.description or "Negative test case"}"""',
                "    with pytest.raises(Exception):",
                f"        {tool.name}(**{kwargs_repr})",
                "",
            ])
        else:
            expected_repr = json.dumps(ex.expected)
            lines.extend([
                f"def {test_fn_name}() -> None:",
                f'    """{ex.description or "Positive test case"}"""',
                f"    result = {tool.name}(**{kwargs_repr})",
                f"    assert result == {expected_repr}",
                "",
            ])

    # Add standard boundary / unicode edge cases
    lines.extend([
        f"def test_{tool.name}_unicode_boundary() -> None:",
        '    """Verifies handling of standard UTF-8 and unicode boundary values."""',
        f'    result = {tool.name}(text="test \\u00e9")' if "text" in tool.input_schema.get("properties", {}) else f"    result = {tool.name}()",
        "    assert result is not None",
        "",
    ])

    return "\n".join(lines)


class TestGenerator:
    def generate_tests_for_spec(self, spec: SkillSpec) -> list[GeneratedFile]:
        """Synthesizes independent unit tests and locks them with cryptographic hashes."""
        test_files: list[GeneratedFile] = []

        for tool in spec.tools:
            code = generate_tool_tests(tool)
            test_files.append(
                GeneratedFile(
                    path=f"tests/test_{tool.name}.py",
                    content=code,
                    is_executable=False,
                )
            )

        return test_files

    @classmethod
    def compute_test_suite_hash(cls, test_files: list[GeneratedFile]) -> str:
        """Computes cryptographic SHA-256 fingerprint of the test suite."""
        combined = "\n---\n".join(f"{tf.path}:{tf.content}" for tf in sorted(test_files, key=lambda f: f.path))
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
