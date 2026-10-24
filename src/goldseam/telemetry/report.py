"""Run report generator formatting compilation history into Markdown and JSON."""

from goldseam.telemetry.run_store import RunRecord


class RunReportGenerator:
    """Generates structured diagnostics and human-readable audit reports for runs."""

    @staticmethod
    def generate_markdown(record: RunRecord) -> str:
        lines: list[str] = [
            f"# Goldseam Compilation Report: `{record.run_id}`",
            "",
            f"- **Status:** `{record.status}`",
            f"- **Source:** `{record.source}`",
            f"- **Created At:** {record.created_at}",
            f"- **Updated At:** {record.updated_at}",
            f"- **Trace Hash:** `{record.trace_hash[:16]}...`" if record.trace_hash else "",
            "",
            "---",
            "",
            "## 1. Diagnostic Summary",
        ]

        diag = record.stage_data.get("diagnosis", {})
        if diag:
            lines.append(f"- **Failure Class:** {diag.get('failure_class', 'N/A')}")
            lines.append(f"- **Root Cause:** {diag.get('root_cause', 'N/A')}")
            lines.append(f"- **Capability Gap:** {diag.get('capability_gap', 'N/A')}")
            lines.append(f"- **Confidence:** {diag.get('confidence', 0.0)}")
        else:
            lines.append("*No diagnostic stage data recorded.*")

        lines.extend([
            "",
            "## 2. Compilation Attempts & Gates",
        ])

        if record.attempts:
            lines.append("| Attempt | Gates Passed | Total Gates | Bundle Hash | Status |")
            lines.append("|---|---|---|---|---|")
            for att in record.attempts:
                passed_gates = sum(1 for g in att.gate_results if g.passed)
                status_icon = "PASS" if att.passed else "FAIL"
                lines.append(
                    f"| {att.attempt_number} | {passed_gates} | {len(att.gate_results)} | `{att.bundle_hash[:12]}` | {status_icon} |"
                )
        else:
            lines.append("*No compilation attempts executed (triage routed or dry-run).*")

        if record.error:
            lines.extend([
                "",
                "## 3. Failure Explanation",
                f"> [!WARNING]\n> {record.error}",
            ])

        return "\n".join(lines)

    @staticmethod
    def generate_json(record: RunRecord) -> str:
        return record.model_dump_json(indent=2)
