"""Semantic versioning and skill compatibility comparator."""

import re
from enum import StrEnum

from goldseam.models.spec import SkillSpec


class BumpType(StrEnum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"
    NONE = "NONE"


class SkillVersionComparator:
    """Compares existing installed SkillSpec with a newly proposed candidate to decide version bump."""

    SEMVER_REGEX = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")

    @classmethod
    def parse_semver(cls, version: str) -> tuple[int, int, int]:
        m = cls.SEMVER_REGEX.match(version.strip())
        if not m:
            return (0, 1, 0)
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    @classmethod
    def bump_version(cls, current_version: str, bump: BumpType) -> str:
        major, minor, patch = cls.parse_semver(current_version)
        if bump == BumpType.MAJOR:
            return f"{major + 1}.0.0"
        elif bump == BumpType.MINOR:
            return f"{major}.{minor + 1}.0"
        elif bump == BumpType.PATCH:
            return f"{major}.{minor}.{patch + 1}"
        return current_version

    @classmethod
    def determine_bump(cls, old_spec: SkillSpec, new_spec: SkillSpec) -> BumpType:
        old_tool_names = {t.name for t in old_spec.tools}
        new_tool_names = {t.name for t in new_spec.tools}

        # Removed existing tools -> Breaking change (MAJOR)
        if not old_tool_names.issubset(new_tool_names):
            return BumpType.MAJOR

        # Added new tools -> Backwards-compatible feature (MINOR)
        if len(new_tool_names) > len(old_tool_names):
            return BumpType.MINOR

        # Same tools: check input schemas for breaking additions
        for old_tool in old_spec.tools:
            new_tool = next((t for t in new_spec.tools if t.name == old_tool.name), None)
            if new_tool:
                old_req = set(old_tool.input_schema.get("required", []))
                new_req = set(new_tool.input_schema.get("required", []))
                if not new_req.issubset(old_req):
                    # Added required parameters -> Breaking change (MAJOR)
                    return BumpType.MAJOR

        # Implementation bugfix or docs improvement (PATCH)
        return BumpType.PATCH
