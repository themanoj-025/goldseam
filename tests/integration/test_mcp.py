"""Integration tests for Model Context Protocol (MCP) server generation."""

from pathlib import Path

from goldseam.models.spec import Example, SideEffect, SkillSpec, ToolSpec
from goldseam.registry.mcp_emitter import MCPEmitter, emit_mcp_server_script


def test_mcp_emitter(tmp_path: Path) -> None:
    tool = ToolSpec(
        name="normalize_whitespace",
        purpose="Collapses multiple whitespace chars.",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "string"},
        side_effects=[SideEffect.NONE],
        examples=[
            Example(inputs={"text": "a   b"}, expected="a b", should_fail=False),
            Example(inputs={"text": "c"}, expected="c", should_fail=False),
            Example(inputs={"text": None}, expected="err", should_fail=True),
        ],
    )
    spec = SkillSpec(
        slug="whitespace-normalizer",
        description="Normalizes messy whitespace.",
        triggers=["normalize whitespace"],
        non_triggers=["sql formatting"],
        tools=[tool],
    )

    script_content = emit_mcp_server_script(spec)
    assert "FastMCP" in script_content
    assert "@mcp.tool" in script_content
    assert "normalize_whitespace_mcp" in script_content

    emitter = MCPEmitter()
    server_path = emitter.emit_server(spec, tmp_path)
    assert server_path.is_file()
    assert (tmp_path / "mcp_server.py").is_file()
