# Model Context Protocol (MCP) Specification & Goldseam Integration Contract

**Specification Baseline:** Model Context Protocol (MCP) by Anthropic  
**Retrieval & Verification Date:** 2026-10-24  
**SDK Requirement:** `mcp>=1.0.0` (FastMCP stdio interface)  
**Status:** Pinned & Verified against Integration Tests (`tests/integration/test_mcp.py`)  

---

## 1. Protocol Architecture & Transports

The Model Context Protocol (MCP) enables LLMs to securely query structured context and execute tools via standardized client-server interfaces:

```
[Agent / LLM Host]  <-- JSON-RPC 2.0 (stdio / SSE) -->  [MCP Server]  <-- In-Memory Call -->  [Pure Tool Functions]
```

Goldseam supports two distinct MCP targets:
1. **Standalone Tool Server Emitter (`MCPEmitter`):** Converts generated skills into standalone, runnable MCP stdio servers (`mcp_server.py`) that wrap pure deterministic functions.
2. **Goldseam Administrative Proposal Server (`GoldseamMCPServer`):** An administrative query server allowing agents to inspect installed skills, verify provenance, and review compilation proposals.

---

## 2. Invariant: Untrusted Agent Isolation

In adherence to **Invariant 1** and **Invariant 6**:
- Untrusted agents invoking tools via MCP may **never** call live skill installation functions directly.
- The `GoldseamMCPServer` exposes only read-only query operations (`list_skills`, `show_skill`, `verify_skill`, `list_proposals`, `explain_run`).
- Skill compilation proposals remain staged in `REVIEW` status until an authorized human executes `goldseam review <RUN_ID> --approve`.

---

## 3. FastMCP Tool Registration Schema

Generated tool servers use FastMCP with standard typing:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Tool Name")

@mcp.tool(name="tool_name", description="Clear human-readable description")
def tool_name_mcp(text: str = "") -> str:
    """Delegates cleanly to pure deterministic function in scripts/."""
    from scripts.tool_name import tool_name
    result = tool_name(text=text)
    return str(result)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## 4. Verification and Conformance Gate

Every emitted MCP server must satisfy:
1. Valid Python syntax conforming to AST security allowlists.
2. Direct invocation capability via stdio transport without hanging.
3. Clean error reporting with serialized JSON-RPC error frames on malformed input.
