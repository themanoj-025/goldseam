"""Unit tests for pluggable extensions, entry points, and trust contracts."""

import pytest

from goldseam.errors import PolicyViolationError
from goldseam.ingest.base import IngestAdapter
from goldseam.plugins import PluginManager
from goldseam.sandbox.base import SandboxRunner


def test_plugin_list() -> None:
    pm = PluginManager()
    plugins = pm.list_plugins()
    assert len(plugins) > 0

    adapter_plugins = [p for p in plugins if p.group == "goldseam.adapters"]
    assert any(p.name == "terminal" for p in adapter_plugins)
    assert any(p.name == "pytest" for p in adapter_plugins)
    assert all(p.trusted for p in adapter_plugins if p.version == "0.1.0")


def test_load_builtin_adapter() -> None:
    pm = PluginManager()
    adapter = pm.load_adapter("terminal")
    assert isinstance(adapter, IngestAdapter)
    assert adapter.name == "terminal_log"



def test_load_builtin_backend() -> None:
    pm = PluginManager()
    runner = pm.load_backend("local")
    assert isinstance(runner, SandboxRunner)
    assert runner.name == "local"


def test_unknown_plugin_rejected() -> None:
    pm = PluginManager()
    with pytest.raises(PolicyViolationError, match="Unknown adapter plugin"):
        pm.load_adapter("nonexistent_unknown_plugin")


def test_untrusted_plugin_blocked_by_default() -> None:
    # Simulates attempt to load an untrusted external plugin without explicit opt-in
    pm = PluginManager(allow_untrusted_plugins=False)
    with pytest.raises(PolicyViolationError):
        pm.load_adapter("arbitrary_external_module")
