"""Unit tests for SARIF export functionality."""

import json
from pathlib import Path

from goldseam.security.sarif import SarifExporter


def test_sarif_export(tmp_path: Path) -> None:
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    # Test valid case
    valid_sarif = SarifExporter.export_verification_findings(skill_dir, valid=True, discrepancies=[])
    assert valid_sarif["version"] == "2.1.0"
    assert len(valid_sarif["runs"][0]["results"]) == 0

    # Test tamper discrepancy
    tamper_sarif = SarifExporter.export_verification_findings(
        skill_dir,
        valid=False,
        discrepancies=["Hash mismatch in scripts/normalize.py", "Untracked file found"],
    )
    assert len(tamper_sarif["runs"][0]["results"]) == 2
    assert tamper_sarif["runs"][0]["results"][0]["level"] == "error"
    assert tamper_sarif["runs"][0]["results"][0]["ruleId"] == "GS001-TAMPER"

    # Test file writing
    out_file = tmp_path / "report.sarif"
    SarifExporter.write_sarif_file(out_file, skill_dir, valid=False, discrepancies=["tamper alert"])
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["version"] == "2.1.0"
