"""Interactive terminal review dashboard for inspectable skill compilation proposals."""

from enum import StrEnum
from typing import Any

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table

from goldseam.models.result import Attempt
from goldseam.telemetry.run_store import RunRecord


class ReviewChoice(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EDIT = "EDIT"
    DEFER = "DEFER"


class ReviewDashboard:
    """Renders comprehensive, human-inspectable review dashboards with Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console(highlight=False)

    def render_overview(self, run: RunRecord) -> RenderableType:
        """Constructs an integrated review panel showing diffs, risks, and verification gates."""
        spec = run.stage_data.get("spec", {})
        risk = spec.get("risk_assessment", {})
        risk_level = risk.get("level", "UNKNOWN") if isinstance(risk, dict) else str(risk)

        # 1. Summary Table
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Field", style="bold cyan")
        summary_table.add_column("Value")

        summary_table.add_row("Run ID", run.run_id)
        summary_table.add_row("Status", run.status)
        summary_table.add_row("Source", run.source)
        summary_table.add_row("Target Skill Slug", spec.get("slug", "unknown"))
        summary_table.add_row("Description", spec.get("description", "N/A"))
        summary_table.add_row("Assessed Risk Level", f"[bold]{risk_level}[/bold]")

        # 2. Gates Table
        gates_table = Table(title="Verified Security & Quality Gates", header_style="bold magenta")
        gates_table.add_column("Gate")
        gates_table.add_column("Status")
        gates_table.add_column("Outcome")
        gates_table.add_column("Duration")

        if run.attempts:
            last_att: Attempt = run.attempts[-1]
            for g in last_att.gate_results:
                status_badge = "[green]PASS[/green]" if g.passed else "[red]FAIL[/red]"
                gates_table.add_row(g.gate, status_badge, str(g.outcome), f"{g.duration_ms:.1f}ms")
        else:
            gates_table.add_row("Static Pre-check", "[yellow]PENDING[/yellow]", "N/A", "0ms")

        # 3. Artifact Files Table
        files_table = Table(title="Generated Bundle Artifacts", header_style="bold blue")
        files_table.add_column("File Path")
        files_table.add_column("Executable")
        files_table.add_column("Size (Bytes)")

        bundle_files: list[Any] = run.stage_data.get("bundle_files", [])
        for f in bundle_files:
            if isinstance(f, dict):
                files_table.add_row(f.get("path", ""), str(f.get("is_executable", False)), str(len(f.get("content", ""))))
            else:
                files_table.add_row(str(f), "False", "N/A")

        # Combine into master panel
        from rich.console import Group

        group = Group(
            summary_table,
            Panel(gates_table, border_style="magenta"),
            Panel(files_table, border_style="blue"),
        )
        return Panel(group, title=f"Goldseam Human Review Dashboard — {run.run_id}", border_style="green")

    def display(self, run: RunRecord) -> None:
        """Renders dashboard to console."""
        panel = self.render_overview(run)
        self.console.print(panel)
