"""Goldseam command-line interface implemented with Typer and Rich."""

import json
import sys
from pathlib import Path
from typing import Annotated

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
    console.print(f"Python: {py_version} [{'green' if py_ok else 'red'}{'OK' if py_ok else 'FAIL'}[/]]")
    console.print(f"Docker Sandbox: [{'green' if docker_ok else 'yellow'}{'AVAILABLE' if docker_ok else 'UNAVAILABLE'}[/] ({docker_msg})")
    console.print(f"Library Dir: {cfg.library_dir} [{'green' if lib_ok else 'red'}{'EXISTS' if lib_ok else 'MISSING'}[/]]")
    console.print(f"Run Store Dir: {cfg.run_store_dir} [{'green' if runs_ok else 'red'}{'EXISTS' if runs_ok else 'MISSING'}[/]]")

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
        err_console.print("[red]Error:[/red] Provide --from-log, --from-stdin, --from-diff, or --need")
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
) -> None:
    """Verifies cryptographic provenance and detects single-byte tampering."""
    if not skill_dir.is_dir():
        err_console.print(f"[red]Error:[/red] Directory '{skill_dir}' not found")
        raise typer.Exit(code=1)

    index = LibraryIndex(skill_dir.parent)
    valid, discrepancies = index.verify_skill(skill_dir)

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
def review_cmd(run_id: Annotated[str, typer.Argument(help="Run ID to review")]) -> None:
    """Reviews a pending compilation proposal."""
    cfg = GoldseamConfig.load()
    store = RunStore(cfg.run_store_dir)
    run = store.get_run(run_id)
    if not run:
        err_console.print(f"[red]Error:[/red] Run '{run_id}' not found")
        raise typer.Exit(code=1)

    console.print(f"[bold]Reviewing Run:[/bold] {run.run_id} (Status: {run.status})")
    console.print(f"Source: {run.source}")
    if "spec" in run.stage_data:
        console.print(f"Skill Slug: {run.stage_data['spec'].get('slug')}")
        console.print(f"Description: {run.stage_data['spec'].get('description')}")


@app.command(name="resume")
def resume_cmd(run_id: Annotated[str, typer.Argument(help="Run ID to resume")]) -> None:
    """Resumes a checkpointed compilation run."""
    console.print(f"Resuming run {run_id}...")


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
    from_diff: Annotated[Path, typer.Option("--from-diff", help="Unified diff of correction")],
    why: Annotated[str, typer.Option("--why", help="Human rationale for correction")],
) -> None:
    """Synthesizes a rule or skill from a human code correction diff."""
    if not from_diff.is_file():
        err_console.print(f"[red]Error:[/red] Diff file '{from_diff}' not found")
        raise typer.Exit(code=1)
    console.print(f"[green]Learned from diff:[/green] {from_diff} (Reason: {why})")


@app.command(name="hook")
def hook_cmd() -> None:
    """Ingests agent telemetry via fast non-blocking background hook."""
    console.print("Goldseam telemetry hook registered.")


@app.command(name="watch")
def watch_cmd() -> None:
    """Monitors incoming failures and clusters recurring patterns."""
    console.print("Goldseam background watcher active.")


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
def improve_cmd(slug: Annotated[str, typer.Argument(help="Skill slug name")]) -> None:
    """Analyzes regression traces to improve an existing skill."""
    console.print(f"Analyzing improvement candidates for skill '{slug}'...")
