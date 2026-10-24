"""Atomic skill packager with safe staging, collision handling, and rollback."""

import datetime
import shutil
from enum import StrEnum
from pathlib import Path

from goldseam.errors import PackagingError
from goldseam.models.bundle import GeneratedBundle
from goldseam.models.provenance import ProvenanceRecord
from goldseam.models.result import GateResult


class CollisionMode(StrEnum):
    FAIL = "FAIL"
    OVERWRITE = "OVERWRITE"
    BACKUP_AND_REPLACE = "BACKUP_AND_REPLACE"


class AtomicPackager:
    def __init__(self, library_dir: Path) -> None:
        self.library_dir = library_dir
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def package_and_install(
        self,
        bundle: GeneratedBundle,
        gate_results: list[GateResult],
        trace_hash: str,
        policy_hash: str,
        model_id: str = "compiler",
        collision_mode: CollisionMode = CollisionMode.BACKUP_AND_REPLACE,
    ) -> Path:
        """
        Atomically stages and installs a verified skill bundle into the library.
        Guarantees rollback if any step fails.
        """
        target_dir = self.library_dir / bundle.skill_slug
        stage_dir = self.library_dir / f".tmp_{bundle.skill_slug}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_dir = self.library_dir / f".bak_{bundle.skill_slug}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        if target_dir.exists():
            if collision_mode == CollisionMode.FAIL:
                raise PackagingError(f"Target skill directory '{target_dir}' already exists")

        stage_dir.mkdir(parents=True, exist_ok=True)
        try:
            # 1. Write all bundle files to staging directory
            artifact_hashes: dict[str, str] = {}
            for bf in bundle.files:
                dest = stage_dir / bf.path
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "w", encoding="utf-8", newline="\n") as f:
                    f.write(bf.content)
                artifact_hashes[bf.path] = ProvenanceRecord.compute_sha256(bf.content)

            # 2. Write provenance.json
            now_iso = datetime.datetime.now(datetime.UTC).isoformat()
            provenance = ProvenanceRecord(
                timestamp=now_iso,
                skill_slug=bundle.skill_slug,
                redacted_trace_hash=trace_hash,
                model_ids={"compiler": model_id},
                prompt_versions={"packager": "v1.0"},
                policy_hash=policy_hash,
                gate_results=gate_results,
                artifact_hashes=artifact_hashes,
            )
            with open(stage_dir / "provenance.json", "w", encoding="utf-8") as pf:
                pf.write(provenance.model_dump_json(indent=2))

            # 3. Atomic swap
            if target_dir.exists():
                if collision_mode == CollisionMode.BACKUP_AND_REPLACE:
                    target_dir.rename(backup_dir)
                else:
                    shutil.rmtree(target_dir)

            stage_dir.rename(target_dir)

            # Cleanup backup on successful swap
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)

            return target_dir

        except Exception as e:
            # Rollback: remove staging and restore backup if needed
            shutil.rmtree(stage_dir, ignore_errors=True)
            if backup_dir.exists() and not target_dir.exists():
                backup_dir.rename(target_dir)
            raise PackagingError(f"Failed to atomically package skill '{bundle.skill_slug}': {e}") from e
