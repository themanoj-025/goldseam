"""Library evolution manager: batch traces, merge/upgrade, test preservation, and retirement suggestions."""

import datetime
from typing import Any

from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import Orchestrator
from goldseam.models.bundle import GeneratedBundle
from goldseam.models.spec import SkillSpec
from goldseam.registry.index import LibraryIndex
from goldseam.registry.versioning import BumpType, SkillVersionComparator
from goldseam.telemetry.run_store import RunRecord, RunStore


class LibraryEvolutionManager:
    """Manages skill lifecycles, upgrades, backwards compatibility, and retirement."""

    def __init__(self, config: GoldseamConfig | None = None) -> None:
        self.config = config or GoldseamConfig.load()
        self.index = LibraryIndex(self.config.library_dir)
        self.run_store = RunStore(self.config.run_store_dir)

    def suggest_retirements(self, days_inactive: int = 30) -> list[dict[str, Any]]:
        """Scans installed skills and suggests retirement/archival for dormant or obsolete skills."""
        installed = self.index.list_skills()
        runs = self.run_store.list_runs()
        now = datetime.datetime.now(datetime.UTC)
        cutoff = now - datetime.timedelta(days=days_inactive)

        suggestions: list[dict[str, Any]] = []

        for skill in installed:
            slug = skill["slug"]
            related_runs = [
                r for r in runs if r.stage_data.get("spec", {}).get("slug") == slug
            ]

            last_activity: datetime.datetime | None = None
            if related_runs:
                try:
                    last_str = related_runs[0].created_at
                    dt = datetime.datetime.fromisoformat(last_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.UTC)
                    last_activity = dt
                except Exception:
                    pass

            if not related_runs:
                suggestions.append(
                    {
                        "slug": slug,
                        "status": "UNVERIFIED_DORMANT",
                        "recommendation": "ARCHIVE",
                        "reason": "No compilation or execution history found in run store.",
                        "days_inactive": None,
                    }
                )
            elif last_activity and last_activity < cutoff:
                days = (now - last_activity).days
                suggestions.append(
                    {
                        "slug": slug,
                        "status": "INACTIVE",
                        "recommendation": "DEPRECATE",
                        "reason": f"Dormant for {days} days exceeding threshold of {days_inactive} days.",
                        "days_inactive": days,
                    }
                )
            else:
                suggestions.append(
                    {
                        "slug": slug,
                        "status": "ACTIVE",
                        "recommendation": "RETAIN",
                        "reason": "Active and verified in current operating window.",
                        "days_inactive": 0 if not last_activity else (now - last_activity).days,
                    }
                )

        return suggestions

    def merge_or_upgrade(
        self,
        existing_slug: str,
        new_spec: SkillSpec,
        new_bundle: GeneratedBundle,
    ) -> GeneratedBundle:
        """Merges a newly generated skill bundle into an existing skill while preserving previous regression tests."""
        existing_skill_dir = self.config.library_dir / existing_slug
        if not existing_skill_dir.is_dir():
            return new_bundle

        # Load existing manifest if available
        old_version = "0.1.0"
        manifest_file = existing_skill_dir / "goldseam.manifest.json"
        if manifest_file.is_file():
            try:
                import json
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                old_version = data.get("version", "0.1.0")
            except Exception:
                pass

        # Calculate semver bump
        bump = SkillVersionComparator.determine_bump(new_spec, new_spec)
        if bump == BumpType.NONE:
            bump = BumpType.PATCH
        new_version = SkillVersionComparator.bump_version(old_version, bump)

        # Merge files, preserving previous tests
        file_map: dict[str, str] = {f.path: f.content for f in new_bundle.files}
        tests_dir = existing_skill_dir / "tests"
        if tests_dir.is_dir():
            for test_file in tests_dir.glob("test_*.py"):
                rel_path = f"tests/prev_{test_file.name}"
                if rel_path not in file_map:
                    file_map[rel_path] = test_file.read_text(encoding="utf-8")

        # Update manifest content with bumped version
        manifest_path = "goldseam.manifest.json"
        if manifest_path in file_map:
            import json
            try:
                m_data = json.loads(file_map[manifest_path])
                m_data["version"] = new_version
                m_data["upgraded_from"] = old_version
                file_map[manifest_path] = json.dumps(m_data, indent=2)
            except Exception:
                pass

        from goldseam.models.bundle import GeneratedFile

        bundle_files = [
            GeneratedFile(path=p, content=c, is_executable=p.startswith("scripts/"))
            for p, c in file_map.items()
        ]
        return GeneratedBundle(skill_slug=new_bundle.skill_slug, files=bundle_files)


    def batch_evolve(self, trace_inputs: list[str]) -> list[RunRecord]:
        """Processes a batch of untrusted failure traces and generates proposals."""
        orch = Orchestrator(config=self.config)
        records: list[RunRecord] = []
        for i, trace in enumerate(trace_inputs):
            rec = orch.run_compilation(
                raw_input=trace,
                source=f"batch_trace_{i}",
                dry_run=True,
                auto_approve=False,
            )
            records.append(rec)
        return records
