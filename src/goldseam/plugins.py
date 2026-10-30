"""Pluggable adapters, sandbox backends, and verification gates with explicit trust contracts."""

import importlib.metadata
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from goldseam.errors import PolicyViolationError
from goldseam.ingest.base import IngestAdapter
from goldseam.sandbox.base import SandboxRunner


class PluginContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=64, description="Plugin identifier")
    group: str = Field(description="Entry point group: goldseam.adapters, goldseam.backends, goldseam.gates")
    version: str = Field(default="1.0.0", description="Plugin semantic version")
    trusted: bool = Field(default=True, description="Whether the plugin is signed or built-in")
    description: str = Field(default="", description="Plugin summary")


class PluginManager:
    """Discovers, validates, and instantiates pluggable extensions with explicit trust boundaries."""

    # Built-in known safe registry mappings
    BUILTIN_ADAPTERS: dict[str, str] = {
        "terminal": "goldseam.ingest.terminal:TerminalLogAdapter",
        "pytest": "goldseam.ingest.pytest_log:PytestLogAdapter",
        "traceback": "goldseam.ingest.traceback_py:TracebackAdapter",
        "claude_code": "goldseam.ingest.claude_code_jsonl:ClaudeCodeJsonlAdapter",
        "git_diff": "goldseam.ingest.git_diff:GitDiffAdapter",
        "need": "goldseam.ingest.plain_need:PlainNeedAdapter",
    }

    BUILTIN_BACKENDS: dict[str, str] = {
        "docker": "goldseam.sandbox.backends.docker:DockerSandboxRunner",
        "local": "goldseam.sandbox.backends.local:LocalSubprocessRunner",
        "bwrap": "goldseam.sandbox.backends.bwrap:BubblewrapSandboxRunner",
    }


    def __init__(self, allow_untrusted_plugins: bool = False) -> None:
        self.allow_untrusted = allow_untrusted_plugins

    def list_plugins(self, group: str | None = None) -> list[PluginContract]:
        """Lists all registered extensions across adapters, backends, and gates."""
        results: list[PluginContract] = []

        if group is None or group == "goldseam.adapters":
            for name, path in self.BUILTIN_ADAPTERS.items():
                results.append(
                    PluginContract(
                        name=name,
                        group="goldseam.adapters",
                        version="0.1.0",
                        trusted=True,
                        description=f"Built-in ingest adapter ({path})",
                    )
                )

        if group is None or group == "goldseam.backends":
            for name, path in self.BUILTIN_BACKENDS.items():
                results.append(
                    PluginContract(
                        name=name,
                        group="goldseam.backends",
                        version="0.1.0",
                        trusted=True,
                        description=f"Built-in sandbox backend ({path})",
                    )
                )

        # Check Python environment entry points
        target_groups = [group] if group else ["goldseam.adapters", "goldseam.backends", "goldseam.gates"]
        for grp in target_groups:
            try:
                eps = importlib.metadata.entry_points(group=grp)
                for ep in eps:
                    results.append(
                        PluginContract(
                            name=ep.name,
                            group=grp,
                            version="external",
                            trusted=False,  # External plugins untrusted by default
                            description=f"External entry point ({ep.value})",
                        )
                    )
            except (KeyError, AttributeError, ValueError):
                pass

        return results


    def load_adapter(self, name: str) -> IngestAdapter:
        """Loads and instantiates an ingest adapter matching the requested name."""
        if name in self.BUILTIN_ADAPTERS:
            mod_name, cls_name = self.BUILTIN_ADAPTERS[name].split(":")
            mod = __import__(mod_name, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            instance: Any = cls()
            if not isinstance(instance, IngestAdapter):
                raise PolicyViolationError(f"Plugin '{name}' does not implement IngestAdapter")
            return instance

        # Try entry points
        try:
            eps = importlib.metadata.entry_points(group="goldseam.adapters")
            for ep in eps:
                if ep.name == name:
                    if not self.allow_untrusted:
                        raise PolicyViolationError(
                            f"External plugin '{name}' blocked by untrusted plugin security policy."
                        )
                    loaded_cls: Any = ep.load()
                    inst = loaded_cls()
                    if not isinstance(inst, IngestAdapter):
                        raise PolicyViolationError(f"Plugin '{name}' does not implement IngestAdapter")
                    return inst
        except Exception as e:
            if isinstance(e, PolicyViolationError):
                raise
            raise PolicyViolationError(f"Failed to load adapter plugin '{name}': {e}") from e

        raise PolicyViolationError(f"Unknown adapter plugin '{name}'")

    def load_backend(self, name: str) -> SandboxRunner:
        """Loads and instantiates a sandbox runner backend."""
        if name in self.BUILTIN_BACKENDS:
            mod_name, cls_name = self.BUILTIN_BACKENDS[name].split(":")
            mod = __import__(mod_name, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            instance: Any = cls()
            if not isinstance(instance, SandboxRunner):
                raise PolicyViolationError(f"Plugin '{name}' does not implement SandboxRunner")
            return instance

        try:
            eps = importlib.metadata.entry_points(group="goldseam.backends")
            for ep in eps:
                if ep.name == name:
                    if not self.allow_untrusted:
                        raise PolicyViolationError(
                            f"External backend plugin '{name}' blocked by untrusted plugin security policy."
                        )
                    loaded_cls: Any = ep.load()
                    inst = loaded_cls()
                    if not isinstance(inst, SandboxRunner):
                        raise PolicyViolationError(f"Plugin '{name}' does not implement SandboxRunner")
                    return inst
        except Exception as e:
            if isinstance(e, PolicyViolationError):
                raise
            raise PolicyViolationError(f"Failed to load backend plugin '{name}': {e}") from e

        raise PolicyViolationError(f"Unknown sandbox backend plugin '{name}'")
