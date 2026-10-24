# Claude Code Plugin & Tool Packaging for Goldseam

This integration package exposes Goldseam's autonomous failure-to-skill compiler directly to Claude Code as an external execution capability.

---

## Tool Definitions

Claude Code can consume Goldseam commands via stdio or subprocess execution:

```json
{
  "name": "goldseam_build",
  "description": "Synthesizes an Agent Skill from a recent failure log or terminal error trace.",
  "parameters": {
    "type": "object",
    "properties": {
      "log_path": {
        "type": "string",
        "description": "Path to the terminal error or trace log"
      },
      "dry_run": {
        "type": "boolean",
        "description": "If true, synthesizes proposal without installing"
      }
    },
    "required": ["log_path"]
  }
}
```

---

## Setup in Claude Code

Add the following to your project `.claude/config.json`:
```json
{
  "tools": [
    {
      "name": "goldseam_compile",
      "command": "uv run goldseam build --from-log {log_path} --dry-run"
    },
    {
      "name": "goldseam_verify",
      "command": "uv run goldseam verify {skill_dir}"
    }
  ]
}
```
