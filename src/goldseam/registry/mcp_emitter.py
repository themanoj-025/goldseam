"""Standalone Model Context Protocol (MCP) server emitter reusing pure tool functions."""

from pathlib import Path

from goldseam.models.spec import SkillSpec


def emit_mcp_server_script(spec: SkillSpec) -> str:
    """Emits a complete, protocol-valid MCP server script using the official FastMCP interface."""
    tool_blocks: list[str] = []

    for tool in spec.tools:
        tool_code = f"""
@mcp.tool(name="{tool.name}", description="{tool.purpose}")
def {tool.name}_mcp(text: str = "") -> str:
    \"\"\"{tool.purpose}\"\"\"
    from scripts.{tool.name} import {tool.name}
    result = {tool.name}(text=text)
    return str(result)
"""
        tool_blocks.append(tool_code)

    all_tools_code = "\n".join(tool_blocks)

    return f'''"""Model Context Protocol (MCP) Server for {spec.slug}."""

import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("{spec.slug.replace('-', ' ').title()}")
{all_tools_code}

if __name__ == "__main__":
    # Runs using stdio transport by default
    mcp.run(transport="stdio")
'''


class MCPEmitter:
    def emit_server(self, spec: SkillSpec, out_dir: Path) -> Path:
        """Writes standalone MCP server script into target directory."""
        out_dir.mkdir(parents=True, exist_ok=True)
        server_path = out_dir / "mcp_server.py"
        content = emit_mcp_server_script(spec)
        with open(server_path, "w", encoding="utf-8") as f:
            f.write(content)
        return server_path
