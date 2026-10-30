"""Provenance attestation models and tamper-detection hashing."""

import hashlib
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from goldseam.models.result import GateResult


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(default="1.0.0", description="Provenance schema version")
    timestamp: str = Field(description="ISO-8601 creation timestamp")
    skill_slug: str = Field(min_length=1, max_length=64, description="Target skill identifier")
    redacted_trace_hash: str = Field(
        min_length=64, max_length=64, description="SHA-256 of the redacted source trace"
    )
    model_ids: dict[str, str] = Field(description="Models employed across pipeline stages")
    prompt_versions: dict[str, str] = Field(
        description="Internal prompt templates and versions utilized"
    )
    policy_hash: str = Field(
        min_length=64, max_length=64, description="SHA-256 of the active security policy.toml"
    )
    gate_results: list[GateResult] = Field(description="Verified gate outcomes at compilation time")
    artifact_hashes: dict[str, str] = Field(
        description="Map of relative file paths to SHA-256 hex digests (excluding provenance.json itself)"
    )

    @classmethod
    def compute_sha256(cls, content: str | bytes) -> str:
        if isinstance(content, str):
            clean_bytes = content.replace("\r\n", "\n").encode("utf-8")
        else:
            clean_bytes = content.replace(b"\r\n", b"\n")
        return hashlib.sha256(clean_bytes).hexdigest()

    def verify_artifacts(self, actual_files: Mapping[str, str | bytes]) -> tuple[bool, list[str]]:
        """
        Verifies actual file contents against attested hashes.
        Returns (is_valid, list_of_discrepancies).
        """
        discrepancies: list[str] = []

        # Check all expected files exist and match
        for rel_path, expected_hash in self.artifact_hashes.items():
            if rel_path not in actual_files:
                discrepancies.append(f"Missing expected artifact: {rel_path}")
                continue
            actual_content = actual_files[rel_path]
            actual_hash = self.compute_sha256(actual_content)
            if actual_hash != expected_hash:
                discrepancies.append(
                    f"Integrity mismatch in '{rel_path}': expected {expected_hash}, got {actual_hash}"
                )

        # Check for unexpected extra files (excluding provenance.json)
        for rel_path in actual_files:
            clean = rel_path.replace("\\", "/")
            if clean in ("provenance.json", ".git", ".DS_Store"):
                continue
            if clean not in self.artifact_hashes:
                discrepancies.append(f"Untracked extra artifact found in bundle: {clean}")

        return len(discrepancies) == 0, discrepancies
