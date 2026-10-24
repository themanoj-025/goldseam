"""Data models for generated skill bundles and file artifacts."""

import re
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


class GeneratedFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(
        min_length=1, max_length=256, description="Relative POSIX path within the skill bundle"
    )
    content: str = Field(description="Text or script contents")
    is_executable: bool = Field(
        default=False, description="Whether file should have executable permissions"
    )

    @field_validator("path")
    @classmethod
    def validate_safe_relative_path(cls, v: str) -> str:
        # Normalize slashes
        clean_path = v.replace("\\", "/")
        if clean_path.startswith("/") or re.match(r"^[a-zA-Z]:", clean_path):
            raise ValueError(f"Path '{v}' must be a relative path, not absolute")

        parts = PurePosixPath(clean_path).parts
        if ".." in parts:
            raise ValueError(f"Path traversal detected in path '{v}'")

        for part in parts:
            stem = part.split(".")[0].upper()
            if stem in WINDOWS_RESERVED_NAMES:
                raise ValueError(f"Path '{v}' contains Windows reserved device name '{part}'")

        return clean_path


class GeneratedBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    skill_slug: str = Field(min_length=1, max_length=64, description="Target skill slug")
    files: list[GeneratedFile] = Field(min_length=1, description="List of generated bundle files")
    description: str = Field(default="", description="Bundle metadata or commit summary")

    @model_validator(mode="after")
    def validate_bundle_constraints(self) -> "GeneratedBundle":
        if len(self.files) > 50:
            raise ValueError(f"Bundle exceeds maximum allowed file count (50): {len(self.files)}")

        total_size = sum(len(f.content.encode("utf-8")) for f in self.files)
        if total_size > 5 * 1024 * 1024:  # 5MB limit
            raise ValueError(f"Bundle total size ({total_size} bytes) exceeds 5MB limit")

        paths = [f.path for f in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Bundle contains duplicate file paths")

        # Must contain at least SKILL.md
        if not any(f.path == "SKILL.md" for f in self.files):
            raise ValueError("Bundle is missing required root 'SKILL.md' file")

        return self

    def get_file(self, path: str) -> GeneratedFile | None:
        clean = path.replace("\\", "/")
        for f in self.files:
            if f.path == clean:
                return f
        return None
