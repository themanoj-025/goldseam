"""Policy packs and reproducible build metadata contracts."""

import hashlib
import platform
import sys

from pydantic import BaseModel, ConfigDict, Field

from goldseam import __version__


class PolicyPack(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(description="Policy pack preset name")
    description: str = Field(description="Policy scope and domain intent")
    allowed_imports: list[str] = Field(description="Allowlisted modules")
    disallowed_calls: list[str] = Field(description="Prohibited dangerous functions")
    network_allowed: bool = Field(default=False, description="Whether network access is permitted")
    max_file_count: int = Field(default=50, description="Maximum bundle files allowed")
    max_file_size_bytes: int = Field(default=5242880, description="Max individual file size (bytes)")
    reproducible_metadata: dict[str, str] = Field(
        default_factory=dict, description="Deterministic environment build metadata"
    )


class PolicyPackManager:
    """Manages curated security policy packs and calculates reproducible build metadata."""

    @classmethod
    def compute_reproducible_metadata(cls) -> dict[str, str]:
        """Calculates deterministic build environment hashes and platform signatures."""
        env_str = f"{__version__}:{sys.version}:{platform.system()}:{platform.machine()}"
        env_hash = hashlib.sha256(env_str.encode("utf-8")).hexdigest()
        return {
            "goldseam_version": __version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "build_env_hash": env_hash,
        }

    @classmethod
    def get_policy_pack(cls, preset: str = "strict") -> PolicyPack:
        metadata = cls.compute_reproducible_metadata()
        p = preset.lower()

        if p == "strict":
            return PolicyPack(
                name="strict",
                description="Zero network access, minimal stdlib imports, aggressive AST call rejection",
                allowed_imports=["re", "json", "math", "datetime", "pathlib", "collections", "typing"],
                disallowed_calls=["eval", "exec", "compile", "__import__", "open", "input"],
                network_allowed=False,
                reproducible_metadata=metadata,
            )
        elif p == "standard":
            return PolicyPack(
                name="standard",
                description="Standard offline tools: allows common parsing stdlib modules",
                allowed_imports=["re", "json", "math", "datetime", "pathlib", "collections", "typing", "csv", "hashlib", "urllib.parse"],
                disallowed_calls=["eval", "exec", "compile", "__import__"],
                network_allowed=False,
                reproducible_metadata=metadata,
            )
        elif p == "data_science":
            return PolicyPack(
                name="data_science",
                description="Scientific computing profile: allows numpy, pandas, and statistical computation",
                allowed_imports=["math", "statistics", "json", "csv", "typing", "collections", "numpy", "pandas"],
                disallowed_calls=["eval", "exec", "compile", "__import__"],
                network_allowed=False,
                reproducible_metadata=metadata,
            )
        elif p == "permissive":
            return PolicyPack(
                name="permissive",
                description="Permissive profile for trusted internal offline scripting",
                allowed_imports=["*"],
                disallowed_calls=["eval", "exec"],
                network_allowed=False,
                reproducible_metadata=metadata,
            )
        else:
            # Fall back to strict (fail-closed)
            return cls.get_policy_pack("strict")
