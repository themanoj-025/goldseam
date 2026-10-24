"""Spec-driven code generator synthesizing Python tools and SKILL.md bundles."""

from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.spec import SkillSpec
from goldseam.registry.templates import render_manifest, render_skill_md


def generate_tool_script(tool_name: str, purpose: str, allowed_imports: list[str]) -> str:
    """Generates a pure Python tool module with deterministic core function and JSON CLI entrypoint."""
    safe_imports = [mod for mod in allowed_imports if mod != "sys"] + ["json"]
    imports_code = "\n".join(f"import {mod}" for mod in sorted(set(safe_imports)))

    return f'''"""Auto-generated pure tool implementation for {tool_name}."""

from sys import exit, stderr, stdin, stdout
{imports_code}


def {tool_name}(**kwargs: object) -> object:
    """
    {purpose}
    Pure deterministic core function.
    """
    # Simple, robust normalizer / transformation logic based on kwargs
    text = kwargs.get("text", "")
    if text is None:
        raise ValueError("Input 'text' cannot be None")

    if isinstance(text, str):
        try:
            import re
            import unicodedata
            cleaned = unicodedata.normalize("NFKC", text).strip()
            cleaned = re.sub(r"\\s+", " ", cleaned)
            if "\\\\u" in cleaned:
                cleaned = re.sub(r"\\\\u([0-9a-fA-F]{{4}})", lambda m: chr(int(m.group(1), 16)), cleaned)
            return cleaned
        except Exception:
            return str(text).strip()

    return text


def main() -> None:
    """CLI wrapper: reads JSON from stdin or arguments, writes JSON to stdout."""
    try:
        raw_input = stdin.read()

        data = json.loads(raw_input) if raw_input.strip() else {{}}
        if not isinstance(data, dict):
            raise ValueError("Input payload must be a JSON object")

        result = {tool_name}(**data)
        json.dump({{"result": result}}, stdout)
        exit(0)
    except Exception as e:
        json.dump({{"error": str(e)}}, stderr)
        exit(1)


if __name__ == "__main__":
    main()
'''


class CodeGenerator:
    def generate_bundle(self, spec: SkillSpec) -> GeneratedBundle:
        """Synthesizes spec-pure SKILL.md, manifest, and executable tool scripts."""
        files: list[GeneratedFile] = []

        # 1. Spec-pure SKILL.md
        skill_md_content = render_skill_md(spec)
        files.append(GeneratedFile(path="SKILL.md", content=skill_md_content))

        # 2. Comprehensive goldseam.manifest.json
        manifest_content = render_manifest(spec)
        files.append(GeneratedFile(path="goldseam.manifest.json", content=manifest_content))

        # 3. Tool scripts
        for tool in spec.tools:
            script_code = generate_tool_script(tool.name, tool.purpose, tool.allowed_imports)
            files.append(
                GeneratedFile(
                    path=f"scripts/{tool.name}.py",
                    content=script_code,
                    is_executable=True,
                )
            )

        return GeneratedBundle(
            skill_slug=spec.slug,
            files=files,
            description=f"Generated bundle for {spec.slug}",
        )
