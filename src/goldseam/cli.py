"""Goldseam command-line interface implemented with Typer and Rich."""

import json
import sys
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from goldseam import __version__
from goldseam.config import GoldseamConfig
from goldseam.core.orchestrator import CompilationState, Orchestrator
from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.git_diff import GitDiffAdapter
from goldseam.ingest.plain_need import PlainNeedAdapter
from goldseam.ingest.pytest_log import PytestLogAdapter
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.registry.index import LibraryIndex
from goldseam.sandbox.backends.docker import DockerSandboxRunner
from goldseam.telemetry.run_store import RunStore

app = typer.Typer(
    name="goldseam",
    help="Failure-to-skill compiler: synthesizes verifiable Agent Skills from untrusted agent traces.",
    no_args_is_help=True,
)

console = Console(highlight=False, soft_wrap=True)
err_console = Console(stderr=True, highlight=False, soft_wrap=True)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"goldseam version {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", help="Show version and exit.", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    pass


@app.command(name="init")
def init_cmd() -> None:
    """Initializes local Goldseam library directories and configuration."""
    cfg = GoldseamConfig.load()
    cfg.library_dir.mkdir(parents=True, exist_ok=True)
    cfg.run_store_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Initialized Goldseam workspace:[/green]\n- Library: {cfg.library_dir}\n- Run Store: {cfg.run_store_dir}")


@app.command(name="doctor")
def doctor_cmd(
    fix: Annotated[bool, typer.Option("--fix", help="Create missing directories")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Emit structured JSON")] = False,
) -> None:
    """Runs environment pre-flight diagnostics (Python, Docker, Directory health)."""
    cfg = GoldseamConfig.load()
    docker_runner = DockerSandboxRunner()
    docker_ok, docker_msg = docker_runner.is_available()

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)

    lib_ok = cfg.library_dir.is_dir()
    runs_ok = cfg.run_store_dir.is_dir()

    if fix:
        cfg.library_dir.mkdir(parents=True, exist_ok=True)
        cfg.run_store_dir.mkdir(parents=True, exist_ok=True)
        lib_ok = cfg.library_dir.is_dir()
        runs_ok = cfg.run_store_dir.is_dir()

    report = {
        "python": {"version": py_version, "ok": py_ok},
        "docker": {"available": docker_ok, "details": docker_msg},
        "directories": {
            "library_dir": {"path": str(cfg.library_dir), "exists": lib_ok},
            "run_store_dir": {"path": str(cfg.run_store_dir), "exists": runs_ok},
        },
        "ready": py_ok and (docker_ok or cfg.allow_weak_sandbox),
    }

    if as_json:
        console.print(json.dumps(report, indent=2))
        raise typer.Exit(code=0)

    console.print("[bold]Goldseam Pre-flight Diagnostics[/bold]")
    py_badge = "[green]OK[/green]" if py_ok else "[red]FAIL[/red]"
    docker_badge = "[green]AVAILABLE[/green]" if docker_ok else "[yellow]UNAVAILABLE[/yellow]"
    lib_badge = "[green]EXISTS[/green]" if lib_ok else "[red]MISSING[/red]"
    runs_badge = "[green]EXISTS[/green]" if runs_ok else "[red]MISSING[/red]"

    console.print(f"Python: {py_version} ({py_badge})")
    console.print(f"Docker Sandbox: {docker_badge} ({docker_msg})")
    console.print(f"Library Dir: {cfg.library_dir} ({lib_badge})")
    console.print(f"Run Store Dir: {cfg.run_store_dir} ({runs_badge})")

    if not docker_ok and not cfg.allow_weak_sandbox:
        console.print("\n[yellow]Notice:[/yellow] Docker daemon is offline. Untrusted skill installations will report BLOCKED without --allow-weak-sandbox.")


@app.command(name="build")
def build_cmd(
    from_log: Annotated[Path | None, typer.Option("--from-log", help="Path to terminal/stdout log")] = None,
    from_stdin: Annotated[bool, typer.Option("--from-stdin", help="Read log from stdin")] = False,
    from_transcript: Annotated[Path | None, typer.Option("--from-transcript", help="Path to agent transcript")] = None,
    from_diff: Annotated[Path | None, typer.Option("--from-diff", help="Path to git diff file")] = None,
    need: Annotated[str | None, typer.Option("--need", help="Synthesize from free-text need")] = None,
    target: Annotated[str, typer.Option("--target", help="Output target: agent-skills, mcp, both")] = "agent-skills",
    out: Annotated[Path | None, typer.Option("--out", help="Output directory")] = None,
    sandbox: Annotated[str, typer.Option("--sandbox", help="Sandbox backend: auto, docker, local")] = "auto",
    allow_weak_sandbox: Annotated[bool, typer.Option("--allow-weak-sandbox", help="Allow unhardened local runner")] = False,
    max_iter: Annotated[int, typer.Option("--max-iter", help="Max repair iterations")] = 3,
    budget: Annotated[float, typer.Option("--budget", help="Max USD budget")] = 1.00,
    model: Annotated[str | None, typer.Option("--model", help="Stage model mapping: STAGE=ID")] = None,
    policy: Annotated[str, typer.Option("--policy", help="Security preset: strict, standard, permissive")] = "strict",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Synthesize proposal without sandbox execution")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Auto-approve if risk is low")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
) -> None:
    """Compiles an untrusted failure trace or need into a verified Agent Skill."""
    # Resolve input source
    raw_content = ""
    source_name = "cli"
    adapter: IngestAdapter = TerminalLogAdapter()

    if from_log:
        if not from_log.is_file():
            err_console.print(f"[red]Error:[/red] Log file '{from_log}' not found")
            raise typer.Exit(code=1)
        raw_content = from_log.read_text(encoding="utf-8")
        source_name = "from_log"
        if "pytest" in raw_content or "FAILURES" in raw_content:
            adapter = PytestLogAdapter()
    elif from_stdin:
        raw_content = sys.stdin.read()
        source_name = "from_stdin"
    elif from_transcript:
        if not from_transcript.is_file():
            err_console.print(f"[red]Error:[/red] Transcript file '{from_transcript}' not found")
            raise typer.Exit(code=1)
        raw_content = from_transcript.read_text(encoding="utf-8")
        source_name = "from_transcript"
        from goldseam.ingest.claude_code_jsonl import ClaudeCodeJsonlAdapter
        adapter = ClaudeCodeJsonlAdapter()
    elif from_diff:
        if not from_diff.is_file():
            err_console.print(f"[red]Error:[/red] Diff file '{from_diff}' not found")
            raise typer.Exit(code=1)
        raw_content = from_diff.read_text(encoding="utf-8")
        source_name = "from_diff"
        adapter = GitDiffAdapter()
    elif need:
        raw_content = need
        source_name = "need"
        adapter = PlainNeedAdapter()
    else:
        err_console.print("[red]Error:[/red] Provide --from-log, --from-stdin, --from-transcript, --from-diff, or --need")
        raise typer.Exit(code=1)

    cfg = GoldseamConfig.load(
        overrides={
            "sandbox_backend": sandbox,
            "allow_weak_sandbox": allow_weak_sandbox,
            "max_repair_iterations": max_iter,
            "budget_usd": budget,
            "policy_preset": policy,
            "library_dir": out or GoldseamConfig.load().library_dir,
            "auto_approve_low_risk": yes,
        }
    )

    orch = Orchestrator(config=cfg, ingest_adapter=adapter)
    record = orch.run_compilation(
        raw_input=raw_content,
        source=source_name,
        dry_run=dry_run,
        auto_approve=yes,
        target=target,
    )

    if as_json:
        console.print(record.model_dump_json(indent=2))
        if record.status in (CompilationState.FAILED, CompilationState.REJECTED):
            raise typer.Exit(code=1)
        if record.status == CompilationState.BLOCKED:
            raise typer.Exit(code=2)
        raise typer.Exit(code=0)

    if record.status == CompilationState.DONE:
        console.print(f"[green]Success:[/green] Run {record.run_id} completed successfully (status: {record.status})")
        if dry_run:
            console.print("[blue]Dry-run proposal synthesized and validated statically.[/blue]")
    elif record.status == CompilationState.BLOCKED:
        console.print(f"[yellow]BLOCKED:[/yellow] {record.error}")
        raise typer.Exit(code=2)
    elif record.status == CompilationState.REVIEW:
        console.print(f"[yellow]Proposal Generated (Awaiting Review):[/yellow] Run ID: {record.run_id}")
        console.print(f"Run 'goldseam review {record.run_id}' to inspect diffs and approve.")
    else:
        console.print(f"[red]Failed:[/red] {record.error}")
        raise typer.Exit(code=1)


@app.command(name="verify")
def verify_cmd(
    skill_dir: Annotated[Path, typer.Argument(help="Path to installed skill directory")],
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
    sarif: Annotated[Path | None, typer.Option("--sarif", help="Export findings to SARIF file")] = None,
) -> None:
    """Verifies cryptographic provenance and detects single-byte tampering."""
    if not skill_dir.is_dir():
        err_console.print(f"[red]Error:[/red] Directory '{skill_dir}' not found")
        raise typer.Exit(code=1)

    index = LibraryIndex(skill_dir.parent)
    valid, discrepancies = index.verify_skill(skill_dir)

    if sarif:
        from goldseam.security.sarif import SarifExporter

        SarifExporter.write_sarif_file(sarif, skill_dir, valid, discrepancies)
        console.print(f"[green]Exported SARIF report to '{sarif}'.[/green]")

    if as_json:
        console.print(json.dumps({"valid": valid, "discrepancies": discrepancies}, indent=2))
        raise typer.Exit(code=0 if valid else 1)

    if valid:
        console.print(f"[green]VERIFIED:[/green] Skill at '{skill_dir}' matches signed provenance attestation.")
    else:
        console.print("[red]TAMPER DETECTED / VERIFICATION FAILED:[/red]\n" + "\n".join(f"- {d}" for d in discrepancies))
        raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd(as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False) -> None:
    """Lists all skills registered in the Goldseam library."""
    cfg = GoldseamConfig.load()
    index = LibraryIndex(cfg.library_dir)
    skills = index.list_skills()

    if as_json:
        console.print(json.dumps(skills, indent=2))
        return

    if not skills:
        console.print("[dim]No skills currently installed in library.[/dim]")
        return

    console.print(f"[bold]Installed Skills ({len(skills)}):[/bold]")
    for s in skills:
        prov_mark = "[green]✓ signed[/green]" if s.get("has_provenance") else "[yellow]unsigned[/yellow]"
        console.print(f"- [bold]{s['slug']}[/bold] ({prov_mark}): {s['description']}")


@app.command(name="show")
def show_cmd(slug: Annotated[str, typer.Argument(help="Skill slug name")]) -> None:
    """Displays detailed metadata, manifest, and provenance for an installed skill."""
    cfg = GoldseamConfig.load()
    index = LibraryIndex(cfg.library_dir)
    skill = index.get_skill(slug)
    if not skill:
        err_console.print(f"[red]Error:[/red] Skill '{slug}' not found")
        raise typer.Exit(code=1)
    console.print(json.dumps(skill, indent=2))


@app.command(name="remove")
def remove_cmd(slug: Annotated[str, typer.Argument(help="Skill slug name")]) -> None:
    """Removes a skill from the library."""
    cfg = GoldseamConfig.load()
    index = LibraryIndex(cfg.library_dir)
    if index.remove_skill(slug):
        console.print(f"[green]Removed skill '{slug}'.[/green]")
    else:
        err_console.print(f"[red]Error:[/red] Skill '{slug}' not found")
        raise typer.Exit(code=1)


@app.command(name="export")
def export_cmd(
    slug: Annotated[str, typer.Argument(help="Skill slug name")],
    out_file: Annotated[Path | None, typer.Option("--out", help="Target archive path (.zip or .tar.gz)")] = None,
) -> None:
    """Exports a skill into a distributable archive."""
    cfg = GoldseamConfig.load()
    index = LibraryIndex(cfg.library_dir)
    dest = out_file or Path(f"{slug}.zip")
    archive = index.export_skill(slug, dest)
    console.print(f"[green]Exported skill '{slug}' to '{archive}'.[/green]")


@app.command(name="review")
def review_cmd(
    run_id: Annotated[str, typer.Argument(help="Run ID to review")],
    approve: Annotated[bool, typer.Option("--approve", help="Approve and install proposal into library")] = False,
    reject: Annotated[str | None, typer.Option("--reject", help="Reject proposal with reason")] = None,
    dashboard: Annotated[bool, typer.Option("--dashboard", help="Render full terminal review dashboard")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
) -> None:
    """Reviews a pending compilation proposal (diffs, declared side-effects, risks, and gate results)."""
    cfg = GoldseamConfig.load()
    orch = Orchestrator(config=cfg)
    run = orch.run_store.get_run(run_id)
    if not run:
        err_console.print(f"[red]Error:[/red] Run '{run_id}' not found")
        raise typer.Exit(code=1)

    if approve:
        if run.status != CompilationState.REVIEW:
            err_console.print(f"[red]Error:[/red] Run '{run_id}' is in status {run.status}, cannot approve.")
            raise typer.Exit(code=1)
        dest = orch.approve_run(run_id)
        if as_json:
            console.print(json.dumps({"status": "DONE", "installed_dir": str(dest)}, indent=2))
        else:
            console.print(f"[green]Approved and installed skill:[/green] '{dest}'")
        return

    if reject is not None:
        if run.status != CompilationState.REVIEW:
            err_console.print(f"[red]Error:[/red] Run '{run_id}' is in status {run.status}, cannot reject.")
            raise typer.Exit(code=1)
        updated = orch.reject_run(run_id, reason=reject)
        if as_json:
            console.print(updated.model_dump_json(indent=2))
        else:
            console.print(f"[yellow]Proposal rejected:[/yellow] {reject}")
        return

    if dashboard:
        from goldseam.registry.dashboard import ReviewDashboard

        dash = ReviewDashboard(console)
        dash.display(run)
        console.print(f"\nTo approve: [bold]goldseam review {run.run_id} --approve[/bold]")
        console.print(f"To reject:  [bold]goldseam review {run.run_id} --reject \"reason\"[/bold]")
        return

    spec = run.stage_data.get("spec", {})
    bundle_files = run.stage_data.get("bundle_files", [])
    diagnosis = run.stage_data.get("diagnosis", {})
    risk = spec.get("risk_assessment", {})

    report = {
        "run_id": run.run_id,
        "status": run.status,
        "source": run.source,
        "slug": spec.get("slug", "unknown"),
        "description": spec.get("description", "N/A"),
        "risk": risk.get("level", "UNKNOWN") if isinstance(risk, dict) else str(risk),
        "files": bundle_files,
        "attempts": len(run.attempts),
    }

    if as_json:
        console.print(json.dumps(report, indent=2))
        return

    console.print(f"[bold]Reviewing Compilation Proposal:[/bold] {run.run_id}")
    console.print(f"- Status: [yellow]{run.status}[/yellow]")
    console.print(f"- Skill Slug: [bold]{spec.get('slug', 'unknown')}[/bold]")
    console.print(f"- Description: {spec.get('description', 'N/A')}")
    risk_level = risk.get("level", "UNKNOWN") if isinstance(risk, dict) else str(risk)
    console.print(f"- Risk Level: [bold]{risk_level}[/bold]")
    console.print(f"- Failure Class: {diagnosis.get('failure_class', 'N/A')}")
    console.print(f"- Generated Files ({len(bundle_files)}): {', '.join(bundle_files)}")
    if run.attempts:
        last_att = run.attempts[-1]
        passed = sum(1 for g in last_att.gate_results if g.passed)
        console.print(f"- Verified Gates: {passed} / {len(last_att.gate_results)} passed")

    console.print(f"\nTo approve: [bold]goldseam review {run.run_id} --approve[/bold]")
    console.print(f"To reject:  [bold]goldseam review {run.run_id} --reject \"reason\"[/bold]")



@app.command(name="resume")
def resume_cmd(
    run_id: Annotated[str, typer.Argument(help="Run ID to resume")],
    yes: Annotated[bool, typer.Option("--yes", help="Auto-approve if in review")] = False,
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
) -> None:
    """Resumes a checkpointed compilation run."""
    cfg = GoldseamConfig.load()
    orch = Orchestrator(config=cfg)
    try:
        updated = orch.resume_compilation(run_id, auto_approve=yes)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Failed to resume run '{run_id}': {e}")
        raise typer.Exit(code=1) from e

    if as_json:
        console.print(updated.model_dump_json(indent=2))
        return

    console.print(f"[green]Resumed Run {run_id}:[/green] Current status: [bold]{updated.status}[/bold]")
    if updated.error:
        console.print(f"- Details: {updated.error}")


@app.command(name="explain")
def explain_cmd(run_id: Annotated[str, typer.Argument(help="Run ID to explain")]) -> None:
    """Explains compilation reasoning and diagnostics for a run."""
    cfg = GoldseamConfig.load()
    store = RunStore(cfg.run_store_dir)
    run = store.get_run(run_id)
    if not run:
        err_console.print(f"[red]Error:[/red] Run '{run_id}' not found")
        raise typer.Exit(code=1)
    console.print(json.dumps(run.stage_data.get("diagnosis", {}), indent=2))


@app.command(name="bench")
def bench_cmd(
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
) -> None:
    """Runs the synthetic golden benchmark suite."""
    sys.path.insert(0, str(Path.cwd()))
    from benchmarks.run_bench import run_benchmark

    console.print("Executing golden benchmark suite across 40+ synthetic cases...")
    report = run_benchmark()
    if as_json:
        console.print(json.dumps(report, indent=2))
    else:
        console.print("[green]Benchmark Completed Successfully![/green]")
        for k, v in report["metrics"].items():
            console.print(f"- {k}: [bold]{v}[/bold]")


@app.command(name="learn")
def learn_cmd(
    from_diff: Annotated[Path | None, typer.Option("--from-diff", help="Unified diff file of correction")] = None,
    before: Annotated[Path | None, typer.Option("--before", help="File state before correction")] = None,
    after: Annotated[Path | None, typer.Option("--after", help="File state after correction")] = None,
    why: Annotated[str, typer.Option("--why", help="Human rationale for correction")] = "",
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Synthesize proposal without installing")] = True,
) -> None:
    """Synthesizes a rule or skill from a human code correction diff or before/after pair."""
    import difflib

    diff_content = ""
    if from_diff:
        if not from_diff.is_file():
            err_console.print(f"[red]Error:[/red] Diff file '{from_diff}' not found")
            raise typer.Exit(code=1)
        diff_content = from_diff.read_text(encoding="utf-8")
    elif before and after:
        if not before.is_file():
            err_console.print(f"[red]Error:[/red] Before file '{before}' not found")
            raise typer.Exit(code=1)
        if not after.is_file():
            err_console.print(f"[red]Error:[/red] After file '{after}' not found")
            raise typer.Exit(code=1)
        before_lines = before.read_text(encoding="utf-8").splitlines(keepends=True)
        after_lines = after.read_text(encoding="utf-8").splitlines(keepends=True)
        diff_content = "".join(
            difflib.unified_diff(
                before_lines, after_lines, fromfile=str(before), tofile=str(after)
            )
        )
    else:
        err_console.print("[red]Error:[/red] Provide either --from-diff or both --before and --after")
        raise typer.Exit(code=1)

    full_prompt = f"Correction Diff:\n{diff_content}\n\nHuman Rationale: {why}"
    cfg = GoldseamConfig.load()
    adapter = GitDiffAdapter()
    orch = Orchestrator(config=cfg, ingest_adapter=adapter)
    record = orch.run_compilation(raw_input=full_prompt, source="learn_diff", dry_run=dry_run)

    if as_json:
        console.print(record.model_dump_json(indent=2))
        return


    console.print(f"[green]Learned from diff:[/green] {from_diff}")
    console.print(f"- Rationale: {why}")
    console.print(f"- Compilation Status: [bold]{record.status}[/bold]")
    if "rule" in record.stage_data:
        rule = record.stage_data["rule"]
        console.print(f"- Rule Synthesized: [bold]{rule.get('title')}[/bold] -> {rule.get('guideline')}")
    elif "spec" in record.stage_data:
        spec = record.stage_data["spec"]
        console.print(f"- Skill Proposed: [bold]{spec.get('slug')}[/bold] -> {spec.get('description')}")


@app.command(name="hook")
def hook_cmd(
    error: Annotated[str | None, typer.Option("--error", help="Error text to spool")] = None,
    context: Annotated[str | None, typer.Option("--context", help="JSON metadata context")] = None,
) -> None:
    """Ingests agent telemetry via fast non-blocking background hook."""
    from goldseam.telemetry.hook import TelemetryHook

    content = error
    if not content:
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()

    if not content:
        console.print("Goldseam telemetry hook ready (provide --error or pipe via stdin).")
        return

    ctx_dict: dict[str, Any] = {}
    if context:
        try:
            ctx_dict = json.loads(context)
        except Exception:
            ctx_dict = {"raw_context": context}

    hook = TelemetryHook()
    hook.record_failure(content, ctx_dict)
    console.print("[green]Recorded failure event to Goldseam hook spool.[/green]")


@app.command(name="watch")
def watch_cmd(
    as_json: Annotated[bool, typer.Option("--json", help="Emit structured JSON")] = False,
) -> None:
    """Monitors incoming failures and clusters recurring patterns."""
    from goldseam.telemetry.watcher import TelemetryWatcher

    watcher = TelemetryWatcher()
    clusters = watcher.cluster_failures()

    if as_json:
        console.print(json.dumps(clusters, indent=2))
        return

    console.print(f"[bold]Goldseam Failure Watcher:[/bold] Found {len(clusters)} recurring error clusters.")
    for sig, entries in clusters.items():
        console.print(f"- Cluster [bold]{sig}[/bold]: {len(entries)} events")
        if entries:
            sample = str(entries[0].get("error_text", ""))[:80]
            console.print(f"  Sample: {sample}...")

    if not clusters:
        console.print("[dim]No failure events recorded in spool. Telemetry spool is clear.[/dim]")


@app.command(name="proposals")
def proposals_cmd() -> None:
    """Lists unreviewed skill proposals."""
    cfg = GoldseamConfig.load()
    store = RunStore(cfg.run_store_dir)
    runs = store.list_runs()
    pending = [r for r in runs if r.status == CompilationState.REVIEW]
    console.print(f"[bold]Pending Proposals ({len(pending)}):[/bold]")
    for r in pending:
        console.print(f"- Run ID: {r.run_id} (Source: {r.source})")


@app.command(name="improve")
def improve_cmd(
    slug: Annotated[str, typer.Argument(help="Skill slug name")],
    as_json: Annotated[bool, typer.Option("--json", help="Structured JSON output")] = False,
    retire_check: Annotated[bool, typer.Option("--retire-check", help="Check retirement/deprecation status")] = False,
) -> None:
    """Analyzes regression traces and lifecycle evolution to improve an existing skill."""
    from goldseam.registry.evolution import LibraryEvolutionManager

    cfg = GoldseamConfig.load()
    evo = LibraryEvolutionManager(cfg)

    if retire_check:
        suggestions = evo.suggest_retirements()
        target_sug = next((s for s in suggestions if s["slug"] == slug), None)
        if as_json:
            console.print(json.dumps(target_sug or {"slug": slug, "status": "UNKNOWN"}, indent=2))
            return
        if target_sug:
            console.print(f"[bold]Retirement Assessment for '{slug}':[/bold]")
            console.print(f"- Status: [bold]{target_sug['status']}[/bold]")
            console.print(f"- Recommendation: [bold]{target_sug['recommendation']}[/bold]")
            console.print(f"- Reason: {target_sug['reason']}")
            return

    index = LibraryIndex(cfg.library_dir)
    skill = index.get_skill(slug)
    if not skill:
        err_console.print(f"[red]Error:[/red] Skill '{slug}' not found in library.")
        raise typer.Exit(code=1)

    store = RunStore(cfg.run_store_dir)
    runs = store.list_runs()
    related_runs = [
        r for r in runs if r.stage_data.get("spec", {}).get("slug") == slug
    ]

    recommendations = [
        "Preserve existing regression test assertions when upgrading",
        "Maintain test suites with new edge-case replays",
        "Verify cryptographic provenance with 'goldseam verify'",
    ]
    report = {
        "slug": slug,
        "description": skill.get("description", "N/A"),
        "related_runs_count": len(related_runs),
        "status": "HEALTHY" if related_runs else "PRISTINE",
        "recommendations": recommendations,
    }

    if as_json:
        console.print(json.dumps(report, indent=2))
        return

    console.print(f"[bold]Skill Improvement Analysis: {slug}[/bold]")
    console.print(f"- Description: {skill.get('description', 'N/A')}")
    console.print(f"- Historical Compilation Runs: {len(related_runs)}")
    console.print("- Recommendations:")
    for rec in recommendations:
        console.print(f"  • {rec}")

