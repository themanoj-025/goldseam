"""Provenance verification and attestation utilities for registered skills."""

from pathlib import Path

from goldseam.models.provenance import ProvenanceRecord


class ProvenanceVerifier:
    """Verifies cryptographic provenance records for installed skill directories."""

    @staticmethod
    def verify_directory(skill_dir: Path) -> tuple[bool, list[str]]:
        prov_file = skill_dir / "provenance.json"
        if not prov_file.is_file():
            return False, ["Missing provenance.json attestation"]

        try:
            record = ProvenanceRecord.model_validate_json(prov_file.read_text(encoding="utf-8"))
        except Exception as e:
            return False, [f"Corrupted provenance.json: {e}"]

        discrepancies: list[str] = []

        # Check each declared artifact hash
        for rel_path, expected_hash in record.artifact_hashes.items():
            artifact_file = skill_dir / rel_path
            if not artifact_file.is_file():
                discrepancies.append(f"Missing recorded file '{rel_path}'")
                continue

            content = artifact_file.read_text(encoding="utf-8")
            actual_hash = ProvenanceRecord.compute_sha256(content)
            if actual_hash != expected_hash:
                discrepancies.append(
                    f"Integrity mismatch in '{rel_path}': expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                )

        return (len(discrepancies) == 0, discrepancies)
