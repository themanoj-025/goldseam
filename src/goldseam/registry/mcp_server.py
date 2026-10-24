"""Goldseam Model Context Protocol (MCP) proposal server."""

from typing import Any

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState
from goldseam.registry.index import LibraryIndex
from goldseam.telemetry.run_store import RunStore


class GoldseamMCPServer:
    """Read-only and proposal-only MCP tool handler.

    Untrusted agents may never call direct installation functions through MCP.
    """

    def __init__(self, config: GoldseamConfig | None = None) -> None:
        self.config = config or GoldseamConfig.load()
        self.index = LibraryIndex(self.config.library_dir)
        self.run_store = RunStore(self.config.run_store_dir)

    def list_skills(self) -> list[dict[str, Any]]:
        """Lists installed skills and their verification status."""
        return self.index.list_skills()

    def show_skill(self, slug: str) -> dict[str, Any] | None:
        """Retrieves metadata and manifest for an installed skill."""
        return self.index.get_skill(slug)

    def verify_skill(self, slug: str) -> dict[str, Any]:
        """Checks cryptographic provenance of an installed skill."""
        skill_dir = self.config.library_dir / slug
        if not skill_dir.is_dir():
            return {"valid": False, "discrepancies": [f"Skill '{slug}' does not exist"]}
        valid, discrepancies = self.index.verify_skill(skill_dir)
        return {"valid": valid, "discrepancies": discrepancies}

    def list_proposals(self) -> list[dict[str, Any]]:
        """Lists unreviewed skill compilation proposals."""
        runs = self.run_store.list_runs()
        pending = [r for r in runs if r.status == CompilationState.REVIEW]
        return [
            {
                "run_id": r.run_id,
                "created_at": r.created_at,
                "source": r.source,
                "slug": r.stage_data.get("spec", {}).get("slug", "unknown"),
            }
            for r in pending
        ]

    def explain_run(self, run_id: str) -> dict[str, Any] | None:
        """Explains diagnostic reasoning and evidence for a specific run."""
        run = self.run_store.get_run(run_id)
        if not run:
            return None
        return {
            "run_id": run.run_id,
            "status": run.status,
            "diagnosis": run.stage_data.get("diagnosis", {}),
            "route": run.stage_data.get("route", {}),
            "attempts_count": len(run.attempts),
        }
