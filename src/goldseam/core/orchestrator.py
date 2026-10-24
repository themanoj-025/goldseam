"""Durable state machine orchestrator managing end-to-end compilation and repair."""

from enum import StrEnum
from pathlib import Path

from goldseam.config import GoldseamConfig
from goldseam.core.generator import CodeGenerator
from goldseam.core.repair import RepairEngine
from goldseam.core.router import CapabilityRouter
from goldseam.core.spec_designer import SpecDesigner
from goldseam.core.testgen import TestGenerator
from goldseam.core.triage import TriageEngine
from goldseam.errors import SandboxBlockedError
from goldseam.ingest.base import IngestAdapter
from goldseam.ingest.terminal import TerminalLogAdapter
from goldseam.llm.base import LLMClient
from goldseam.models.bundle import GeneratedBundle, GeneratedFile
from goldseam.models.diagnosis import Diagnosis, Route
from goldseam.models.provenance import ProvenanceRecord
from goldseam.models.result import Attempt, GateResult
from goldseam.models.spec import RiskLevel, SkillSpec
from goldseam.models.trace import NormalizedTrace
from goldseam.quality.claims_audit import ClaimsAuditor
from goldseam.registry.mcp_emitter import emit_mcp_server_script
from goldseam.registry.packager import AtomicPackager, CollisionMode
from goldseam.sandbox.base import SandboxRunner
from goldseam.sandbox.runner import get_sandbox_runner
from goldseam.sandbox.temp_env import staging_environment
from goldseam.security.import_policy import SecurityPolicy
from goldseam.security.validator import StaticSecurityValidator
from goldseam.telemetry.run_store import RunRecord, RunStore


class CompilationState(StrEnum):
    INGEST = "INGEST"
    TRIAGE = "TRIAGE"
    ROUTE = "ROUTE"
    SPEC = "SPEC"
    GENERATE = "GENERATE"
    STATIC_GATE = "STATIC_GATE"
    TESTGEN = "TESTGEN"
    SANDBOX = "SANDBOX"
    QUALITY = "QUALITY"
    REPAIR = "REPAIR"
    REVIEW = "REVIEW"
    PACKAGE = "PACKAGE"
    DONE = "DONE"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class Orchestrator:
    def __init__(
        self,
        config: GoldseamConfig | None = None,
        llm_client: LLMClient | None = None,
        sandbox_runner: SandboxRunner | None = None,
        run_store: RunStore | None = None,
        ingest_adapter: IngestAdapter | None = None,
        policy: SecurityPolicy | None = None,
    ) -> None:
        self.config = config or GoldseamConfig.load()
        self.policy = policy or SecurityPolicy.load_default()
        self.run_store = run_store or RunStore(self.config.run_store_dir)
        self.ingest_adapter = ingest_adapter or TerminalLogAdapter()
        self.sandbox_runner = sandbox_runner or get_sandbox_runner(
            preference=self.config.sandbox_backend,
            allow_weak=self.config.allow_weak_sandbox,
            config=self.config,
        )

        from goldseam.llm.fake import FakeLLMClient
        self.llm_client = llm_client or FakeLLMClient()

        self.triage_engine = TriageEngine(self.llm_client)
        self.router = CapabilityRouter()
        self.spec_designer = SpecDesigner(self.llm_client, self.policy)
        self.generator = CodeGenerator()
        self.testgen = TestGenerator()
        self.validator = StaticSecurityValidator(self.policy, self.config.policy_preset)
        self.repair_engine = RepairEngine(self.llm_client, self.config.max_repair_iterations)
        self.claims_auditor = ClaimsAuditor()

    def run_compilation(
        self,
        raw_input: str | Path,
        source: str = "terminal_log",
        dry_run: bool = False,
        auto_approve: bool = False,
        target: str = "agent-skills",
    ) -> RunRecord:
        """Executes the failure-to-skill compilation pipeline."""
        record = self.run_store.create_run(source=source)

        try:
            # 1. INGEST & REDACT
            record.status = CompilationState.INGEST
            trace: NormalizedTrace = self.ingest_adapter.ingest(raw_input)
            import hashlib
            import json
            trace_data = json.dumps([e.model_dump() for e in trace.events], sort_keys=True)
            record.trace_hash = hashlib.sha256(trace_data.encode("utf-8")).hexdigest()
            record.stage_data["trace"] = trace.model_dump()
            self.run_store.save_run(record)

            # Security gate: quarantine prompt injection and instruction overrides before processing
            if trace.injection_flags:
                record.status = CompilationState.REJECTED
                record.error = f"Quarantined prompt injection detected in trace: {trace.injection_flags}"
                record.stage_data["route"] = {
                    "route": Route.DISCARD.value,
                    "rationale": f"Quarantined prompt injection: {trace.injection_flags}",
                }
                self.run_store.save_run(record)
                return record

            # 2. TRIAGE
            record.status = CompilationState.TRIAGE
            diagnosis: Diagnosis = self.triage_engine.triage(trace)
            record.stage_data["diagnosis"] = diagnosis.model_dump()
            self.run_store.save_run(record)

            # 3. ROUTE
            record.status = CompilationState.ROUTE
            route, rationale = self.router.route(diagnosis)
            record.stage_data["route"] = {"route": route.value, "rationale": rationale}
            self.run_store.save_run(record)

            if route == Route.DISCARD:
                record.status = CompilationState.DONE
                record.error = f"Triage routed to DISCARD: {rationale}"
                self.run_store.save_run(record)
                return record

            if route == Route.RULE_ONLY:
                record.status = CompilationState.DONE
                record.stage_data["rule"] = {
                    "title": diagnosis.failure_class,
                    "guideline": diagnosis.root_cause,
                    "rationale": rationale,
                }
                self.run_store.save_run(record)
                return record

            # 4. SPEC
            record.status = CompilationState.SPEC
            spec: SkillSpec = self.spec_designer.design_spec(trace, diagnosis)
            record.stage_data["spec"] = spec.model_dump()
            self.run_store.save_run(record)

            # 5. GENERATE
            record.status = CompilationState.GENERATE
            bundle: GeneratedBundle = self.generator.generate_bundle(spec)

            # 6. TESTGEN
            record.status = CompilationState.TESTGEN
            test_files = self.testgen.generate_tests_for_spec(spec)
            bundle_files = list(bundle.files) + test_files
            if target in ("mcp", "both"):
                bundle_files.append(
                    GeneratedFile(
                        path="mcp_server.py",
                        content=emit_mcp_server_script(spec),
                        is_executable=True,
                    )
                )
            bundle = GeneratedBundle(
                skill_slug=bundle.skill_slug,
                files=bundle_files,
                description=bundle.description,
            )
            record.stage_data["bundle_files"] = [f.path for f in bundle.files]
            record.stage_data["bundle"] = bundle.model_dump()
            self.run_store.save_run(record)

            # 7. STATIC GATE & SANDBOX EXECUTION (WITH BOUNDED REPAIR LOOP)
            attempt_number = 1
            bundle_passed = False

            while attempt_number <= self.config.max_repair_iterations:
                record.status = CompilationState.STATIC_GATE
                static_results = self.validator.validate_bundle(bundle)

                # If static gates fail, attempt repair immediately
                if not all(gr.passed for gr in static_results):
                    bundle = self.repair_engine.repair_bundle(
                        spec, bundle, static_results, attempt_number
                    )
                    attempt_number += 1
                    continue

                if dry_run:
                    bundle_passed = True
                    break

                # Execute tests in Sandbox
                record.status = CompilationState.SANDBOX
                with staging_environment(bundle) as stage_dir:
                    sandbox_res = self.sandbox_runner.run(
                        stage_dir,
                        timeout_sec=self.config.docker_timeout_sec,
                        memory_limit=self.config.docker_memory_limit,
                    )

                gate_res = GateResult(
                    gate="sandbox_tests",
                    passed=sandbox_res.exit_code == 0,
                    outcome=sandbox_res.outcome,
                    evidence=sandbox_res.stdout + "\n" + sandbox_res.stderr,
                    duration_ms=sandbox_res.duration_ms,
                )

                attempt_record = Attempt(
                    attempt_number=attempt_number,
                    bundle_hash=ProvenanceRecord.compute_sha256(
                        "\n".join(f.content for f in bundle.files)
                    ),
                    gate_results=static_results + [gate_res],
                    passed=gate_res.passed,
                )
                record.attempts.append(attempt_record)
                self.run_store.save_run(record)

                if gate_res.passed:
                    bundle_passed = True
                    break

                # Failing tests trigger repair engine
                record.status = CompilationState.REPAIR
                bundle = self.repair_engine.repair_bundle(
                    spec, bundle, [gate_res], attempt_number
                )
                attempt_number += 1

            if not bundle_passed and not dry_run:
                record.status = CompilationState.FAILED
                record.error = "Failed to synthesize passing bundle within repair limits."
                self.run_store.save_run(record)
                return record

            # 8. QUALITY AUDIT
            record.status = CompilationState.QUALITY
            claims_pass, claims_warnings = self.claims_auditor.audit_claims(spec)
            record.stage_data["quality"] = {
                "claims_passed": claims_pass,
                "warnings": claims_warnings,
            }
            self.run_store.save_run(record)

            # 9. REVIEW
            if dry_run:
                record.status = CompilationState.DONE
                record.stage_data["dry_run"] = True
                self.run_store.save_run(record)
                return record

            record.status = CompilationState.REVIEW
            can_auto_approve = (
                auto_approve
                and self.config.auto_approve_low_risk
                and spec.risk_assessment is not None
                and spec.risk_assessment.level == RiskLevel.LOW
            )

            if not can_auto_approve:
                # Remains in REVIEW state until human approval CLI command
                self.run_store.save_run(record)
                return record

            # 10. PACKAGE & INSTALL
            record.status = CompilationState.PACKAGE
            packager = AtomicPackager(self.config.library_dir)
            packager.package_and_install(
                bundle=bundle,
                gate_results=record.attempts[-1].gate_results if record.attempts else [],
                trace_hash=record.trace_hash,
                policy_hash=self.policy.policy_hash,
                model_id=self.llm_client.name,
                collision_mode=CollisionMode.BACKUP_AND_REPLACE,
            )

            record.status = CompilationState.DONE
            self.run_store.save_run(record)
            return record

        except SandboxBlockedError as e:
            record.status = CompilationState.BLOCKED
            record.error = str(e)
            self.run_store.save_run(record)
            return record
        except Exception as e:
            record.status = CompilationState.FAILED
            record.error = str(e)
            self.run_store.save_run(record)
            return record

    def approve_run(self, run_id: str) -> Path:
        """Approves a proposal currently in REVIEW state, atomically installing it into library."""
        record = self.run_store.get_run(run_id)
        if not record:
            raise ValueError(f"Run record '{run_id}' not found")
        if record.status != CompilationState.REVIEW:
            raise ValueError(f"Run '{run_id}' is in state {record.status}, expected REVIEW")

        spec_data = record.stage_data.get("spec")
        bundle_data = record.stage_data.get("bundle")
        if not spec_data or not bundle_data:
            raise ValueError(f"Run '{run_id}' is missing spec or bundle stage data")

        bundle = GeneratedBundle(**bundle_data)
        packager = AtomicPackager(self.config.library_dir)
        dest = packager.package_and_install(
            bundle=bundle,
            gate_results=record.attempts[-1].gate_results if record.attempts else [],
            trace_hash=record.trace_hash,
            policy_hash=self.policy.policy_hash,
            model_id=self.llm_client.name,
            collision_mode=CollisionMode.BACKUP_AND_REPLACE,
        )
        record.status = CompilationState.DONE
        self.run_store.save_run(record)
        return dest

    def reject_run(self, run_id: str, reason: str = "Rejected by human reviewer") -> RunRecord:
        """Rejects a proposal currently in REVIEW state."""
        record = self.run_store.get_run(run_id)
        if not record:
            raise ValueError(f"Run record '{run_id}' not found")
        record.status = CompilationState.REJECTED
        record.error = reason
        self.run_store.save_run(record)
        return record

    def resume_compilation(self, run_id: str, auto_approve: bool = False) -> RunRecord:
        """Resumes a checkpointed compilation run from its last durable state."""
        record = self.run_store.get_run(run_id)
        if not record:
            raise ValueError(f"Run record '{run_id}' not found in run store")

        if record.status == CompilationState.DONE:
            return record

        if record.status == CompilationState.REVIEW:
            if auto_approve or self.config.auto_approve_low_risk:
                self.approve_run(run_id)
                updated = self.run_store.get_run(run_id)
                return updated or record
            return record

        # If interrupted before review or completion, re-run from checkpointed trace
        trace_data = record.stage_data.get("trace")
        if trace_data:
            trace = NormalizedTrace(**trace_data)
            raw_text = "\n".join(e.text for e in trace.events)
            return self.run_compilation(raw_input=raw_text, source=record.source, auto_approve=auto_approve)

        return record
