"""Goldseam Model Context Protocol (MCP) proposal server with rate and budget caps."""

import time
from typing import Any

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState, Orchestrator
from goldseam.registry.index import LibraryIndex
from goldseam.telemetry.run_store import RunStore


class GoldseamMCPServer:
    """Read-only and proposal-only MCP tool handler with rate and budget caps.

    Untrusted agents may never call direct installation functions through MCP.
    """

    def __init__(
        self,
        config: GoldseamConfig | None = None,
        max_proposals_per_hour: int = 10,
        max_budget_per_proposal: float = 2.00,
    ) -> None:
        self.config = config or GoldseamConfig.load()
        self.index = LibraryIndex(self.config.library_dir)
        self.run_store = RunStore(self.config.run_store_dir)
        self.max_proposals_per_hour = max_proposals_per_hour
        self.max_budget_per_proposal = max_budget_per_proposal
        self._proposal_timestamps: list[float] = []

    def _check_rate_limit(self) -> bool:
        """Returns True if within rate limit, False if rate limited."""
        now = time.time()
        window_start = now - 3600.0
        self._proposal_timestamps = [t for t in self._proposal_timestamps if t > window_start]
        if len(self._proposal_timestamps) >= self.max_proposals_per_hour:
            return False
        self._proposal_timestamps.append(now)
        return True

    def propose_skill(self, input_text: str, source: str = "mcp_agent") -> dict[str, Any]:
        """Synthesizes a skill proposal candidate in proposal-only mode with rate & budget caps.

        Does not install into the active library; requires separate human approval.
        """
        if not self._check_rate_limit():
            return {
                "status": "RATE_LIMITED",
                "error": f"Exceeded maximum proposal rate limit ({self.max_proposals_per_hour} per hour).",
                "installed": False,
            }

        if self.config.budget_usd > self.max_budget_per_proposal:
            return {
                "status": "BUDGET_EXCEEDED",
                "error": f"Requested proposal budget exceeds server cap (${self.max_budget_per_proposal:.2f}).",
                "installed": False,
            }

        orch = Orchestrator(config=self.config)
        record = orch.run_compilation(
            raw_input=input_text,
            source=source,
            dry_run=True,
            auto_approve=False,
        )

        spec = record.stage_data.get("spec", {})
        return {
            "status": "PROPOSED",
            "run_id": record.run_id,
            "slug": spec.get("slug", "unknown"),
            "description": spec.get("description", "N/A"),
            "installed": False,
            "review_required": True,
            "error": record.error,
        }

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
