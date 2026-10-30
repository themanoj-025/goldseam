"""Skill library index manager for listing, inspection, export, and tamper verification."""

import json
import shutil
from pathlib import Path

from goldseam.models.provenance import ProvenanceRecord
from goldseam.security.skillmd_lint import parse_skill_md


class LibraryIndex:
    def __init__(self, library_dir: Path) -> None:
        self.library_dir = library_dir
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> list[dict[str, object]]:
        """Lists all installed skills in the library with parsed metadata."""
        skills: list[dict[str, object]] = []
        if not self.library_dir.is_dir():
            return skills

        for entry in self.library_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                skill_info = self.get_skill(entry.name)
                if skill_info:
                    skills.append(skill_info)

        skills.sort(key=lambda s: str(s.get("slug", "")))
        return skills

    def get_skill(self, slug: str) -> dict[str, object] | None:
        """Retrieves detailed metadata for a registered skill."""
        skill_dir = self.library_dir / slug
        if not skill_dir.is_dir():
            return None

        manifest_file = skill_dir / "goldseam.manifest.json"
        skill_md_file = skill_dir / "SKILL.md"
        provenance_file = skill_dir / "provenance.json"

        manifest_data: dict[str, object] = {}
        if manifest_file.is_file():
            try:
                with open(manifest_file, encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception:
                pass

        description = ""
        if skill_md_file.is_file():
            try:
                content = skill_md_file.read_text(encoding="utf-8")
                frontmatter, _ = parse_skill_md(content)
                description = str(frontmatter.get("description", ""))
            except Exception:
                pass

        has_provenance = provenance_file.is_file()

        return {
            "slug": slug,
            "path": str(skill_dir),
            "description": description or manifest_data.get("description", ""),
            "manifest": manifest_data,
            "has_provenance": has_provenance,
        }

    def remove_skill(self, slug: str) -> bool:
        """Removes a skill from the library."""
        skill_dir = self.library_dir / slug
        if skill_dir.is_dir():
            shutil.rmtree(skill_dir)
            return True
        return False

    def verify_skill(self, skill_dir: Path) -> tuple[bool, list[str]]:
        """
        Cryptographically verifies the integrity and provenance of an installed skill directory.
        Detects single-byte tampering, missing files, or untracked additions.
        """
        prov_file = skill_dir / "provenance.json"
        if not prov_file.is_file():
            return False, ["Missing required 'provenance.json' attestation file"]

        try:
            with open(prov_file, encoding="utf-8") as f:
                prov_data = json.load(f)
            record = ProvenanceRecord(**prov_data)
        except Exception as e:
            return False, [f"Failed to parse provenance.json: {e}"]

        actual_files: dict[str, bytes] = {}
        for p in skill_dir.rglob("*"):
            if p.is_file():
                rel_path = p.relative_to(skill_dir).as_posix()
                actual_files[rel_path] = p.read_bytes()

        return record.verify_artifacts(actual_files)

    def export_skill(self, slug: str, export_archive: Path) -> Path:
        """Exports a skill directory into a compressed zip archive."""
        skill_dir = self.library_dir / slug
        if not skill_dir.is_dir():
            raise FileNotFoundError(f"Skill '{slug}' does not exist in library")

        base_name = export_archive.with_suffix("")
        format_type = "zip" if export_archive.suffix == ".zip" else "gztar"
        archive_path = shutil.make_archive(str(base_name), format_type, root_dir=str(skill_dir))
        return Path(archive_path)
