"""Configuration management with precedence: CLI > Env > Config File > Defaults."""

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class GoldseamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    library_dir: Path = Field(
        default_factory=lambda: Path.home() / ".goldseam" / "skills",
        description="Path to installed agent skills directory",
    )
    run_store_dir: Path = Field(
        default_factory=lambda: Path.home() / ".goldseam" / "runs",
        description="Path to durable sanitized run store",
    )
    sandbox_backend: str = Field(
        default="auto", description="Sandbox backend preference: auto, docker, local, bwrap"
    )
    allow_weak_sandbox: bool = Field(
        default=False,
        description="Explicit opt-in permitting weak local subprocess runner for trusted fixtures",
    )
    max_repair_iterations: int = Field(
        default=3, ge=0, le=10, description="Maximum iterations for self-repair loop"
    )
    budget_usd: float = Field(
        default=1.00, ge=0.0, description="Maximum dollar budget for external LLM calls per run"
    )
    default_provider: str = Field(
        default="fake", description="Default LLM provider adapter: fake, openai, anthropic, ollama"
    )
    policy_preset: str = Field(
        default="strict", description="Security policy preset: strict, standard, permissive"
    )
    auto_approve_low_risk: bool = Field(
        default=False,
        description="Allow auto-approval only for LOW risk proposals when --yes is also passed",
    )
    docker_image: str = Field(
        default="goldseam-sandbox:latest", description="Docker sandbox container image tag"
    )
    docker_timeout_sec: int = Field(
        default=30, ge=1, le=300, description="Sandbox wall-clock execution timeout in seconds"
    )
    docker_memory_limit: str = Field(default="512m", description="Sandbox container memory quota")

    @classmethod
    def load(
        cls, config_path: Path | None = None, overrides: dict[str, object] | None = None
    ) -> "GoldseamConfig":
        """Loads configuration merging Defaults < Config File < Env Vars < Overrides."""
        data: dict[str, object] = {}

        # 1. Check config file
        resolved_path = config_path or (Path.home() / ".goldseam" / "config.toml")
        if resolved_path.is_file():
            try:
                with open(resolved_path, "rb") as f:
                    file_data = tomllib.load(f)
                    data.update(file_data.get("goldseam", file_data))
            except Exception:
                pass

        # 2. Check environment variables
        env_mappings: dict[str, tuple[str, type]] = {
            "GOLDSEAM_LIBRARY_DIR": ("library_dir", Path),
            "GOLDSEAM_RUN_STORE_DIR": ("run_store_dir", Path),
            "GOLDSEAM_SANDBOX_BACKEND": ("sandbox_backend", str),
            "GOLDSEAM_ALLOW_WEAK_SANDBOX": ("allow_weak_sandbox", bool),
            "GOLDSEAM_MAX_REPAIR_ITERATIONS": ("max_repair_iterations", int),
            "GOLDSEAM_BUDGET_USD": ("budget_usd", float),
            "GOLDSEAM_DEFAULT_PROVIDER": ("default_provider", str),
            "GOLDSEAM_POLICY_PRESET": ("policy_preset", str),
            "GOLDSEAM_AUTO_APPROVE_LOW_RISK": ("auto_approve_low_risk", bool),
            "GOLDSEAM_DOCKER_IMAGE": ("docker_image", str),
            "GOLDSEAM_DOCKER_TIMEOUT_SEC": ("docker_timeout_sec", int),
        }

        for env_var, (field_name, field_type) in env_mappings.items():
            val = os.environ.get(env_var)
            if val is not None:
                if field_type is bool:
                    data[field_name] = val.lower() in ("1", "true", "yes")
                elif field_type is Path:
                    data[field_name] = Path(val)
                elif field_type is int:
                    data[field_name] = int(val)
                elif field_type is float:
                    data[field_name] = float(val)
                else:
                    data[field_name] = val

        # 3. Apply explicit overrides (e.g. from CLI flags)
        if overrides:
            for k, v in overrides.items():
                if v is not None:
                    data[k] = v

        return cls(**data)  # type: ignore[arg-type]
