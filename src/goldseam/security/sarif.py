"""SARIF (Static Analysis Results Interchange Format) exporter for Goldseam security findings."""

import json
from pathlib import Path
from typing import Any

from goldseam import __version__


class SarifExporter:
    """Exports AST visitor violations and provenance verification discrepancies to SARIF v2.1.0."""

    SCHEMA_URI = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

    @classmethod
    def export_verification_findings(
        cls,
        skill_dir: Path,
        valid: bool,
        discrepancies: list[str],
    ) -> dict[str, Any]:
        results = []
        for idx, disc in enumerate(discrepancies):
            rule_id = "GS001-TAMPER" if "tamper" in disc.lower() or "mismatch" in disc.lower() else "GS002-POLICY"
            level = "error" if not valid else "warning"
            results.append({
                "ruleId": rule_id,
                "ruleIndex": idx,
                "level": level,
                "message": {"text": disc},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": str(skill_dir.as_posix())},
                            "region": {"startLine": 1, "startColumn": 1},
                        }
                    }
                ],
            })

        sarif_log = {
            "$schema": cls.SCHEMA_URI,
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Goldseam Security Verifier",
                            "version": __version__,
                            "informationUri": "https://github.com/themanoj-025/goldseam",
                            "rules": [
                                {
                                    "id": "GS001-TAMPER",
                                    "name": "ProvenanceTamperDetected",
                                    "shortDescription": {"text": "File hash does not match signed provenance record"},
                                },
                                {
                                    "id": "GS002-POLICY",
                                    "name": "SecurityPolicyViolation",
                                    "shortDescription": {"text": "AST or import security policy violation detected"},
                                },
                            ],
                        }
                    },
                    "results": results,
                }
            ],
        }
        return sarif_log

    @classmethod
    def write_sarif_file(
        cls,
        out_path: Path,
        skill_dir: Path,
        valid: bool,
        discrepancies: list[str],
    ) -> None:
        sarif_data = cls.export_verification_findings(skill_dir, valid, discrepancies)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(sarif_data, indent=2), encoding="utf-8")
