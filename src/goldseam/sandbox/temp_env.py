"""Secure staging environment manager for sandboxed test execution."""

import os
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from goldseam.errors import SandboxError
from goldseam.models.bundle import WINDOWS_RESERVED_NAMES, GeneratedBundle


@contextmanager
def staging_environment(bundle: GeneratedBundle) -> Generator[Path, None, None]:
    """
    Creates an isolated disposable staging directory, writes bundle files safely,
    yields the staging Path, and guarantees complete cleanup upon exit.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="goldseam_stage_"))
    try:
        for f in bundle.files:
            clean_rel = f.path.replace("\\", "/")
            parts = clean_rel.split("/")

            # Security sanity checks
            if any(p in ("..", ".", "") for p in parts):
                raise SandboxError(f"Illegal path component in '{f.path}'")

            for part in parts:
                stem = part.split(".")[0].upper()
                if stem in WINDOWS_RESERVED_NAMES:
                    raise SandboxError(f"Illegal reserved device name in '{f.path}'")

            target_path = temp_dir / clean_rel
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with open(target_path, "w", encoding="utf-8") as out_f:
                out_f.write(f.content)

            if f.is_executable and hasattr(os, "chmod"):
                try:
                    os.chmod(target_path, 0o755)
                except OSError:
                    pass

        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
