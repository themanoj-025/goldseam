"""SkillSpec designer synthesizing formal capability specifications."""

import hashlib
import json

from goldseam.llm.base import LLMClient
from goldseam.models.diagnosis import Diagnosis
from goldseam.models.spec import ReplayOracle, SkillSpec
from goldseam.models.trace import NormalizedTrace
from goldseam.security.import_policy import SecurityPolicy

SPEC_PROMPT_TEMPLATE = """You are a software architect synthesizing a typed capability specification (SkillSpec).
Based on the following diagnosed capability gap, design a complete, typed, robust SkillSpec.

Taxonomic Class: {failure_class}
Root Cause: {root_cause}
Capability Gap: {capability_gap}
Normalized Error: {error_signature}

Requirements:
1. Valid lowercase hyphenated slug (max 64 chars, e.g. 'json-unicode-cleaner').
2. Clear description (max 1024 chars) explaining what the skill does and when to activate.
3. Explicit trigger keywords/phrases and non-trigger boundaries.
4. One or more ToolSpecs, each with:
   - Valid Python identifier name
   - Purpose statement
   - Input and Output JSON Schemas
   - Explicit SideEffects (default NONE)
   - Allowed import modules from pure computation library
   - At least 3 examples with >= 1 negative example (should_fail=True)
"""


class SpecDesigner:
    def __init__(self, llm_client: LLMClient, policy: SecurityPolicy | None = None) -> None:
        self.llm_client = llm_client
        self.policy = policy or SecurityPolicy.load_default()

    def design_spec(self, trace: NormalizedTrace, diagnosis: Diagnosis) -> SkillSpec:
        """Synthesizes and validates a typed SkillSpec contract."""
        prompt = SPEC_PROMPT_TEMPLATE.format(
            failure_class=diagnosis.failure_class,
            root_cause=diagnosis.root_cause,
            capability_gap=diagnosis.capability_gap,
            error_signature=trace.error_signature,
        )

        response = self.llm_client.complete_structured(prompt, SkillSpec)
        spec = response.content

        # 1. Deterministically assess and attach trusted RiskAssessment
        all_side_effects = [s for tool in spec.tools for s in tool.side_effects]
        all_imports = [imp for tool in spec.tools for imp in tool.allowed_imports]
        trusted_risk = self.policy.evaluate_risk(
            declared_side_effects=all_side_effects,
            imported_modules=all_imports,
            preset="strict",
        )

        # 2. Build cryptographically locked ReplayOracle from trace
        trace_data = json.dumps([e.model_dump() for e in trace.events], sort_keys=True)
        trace_hash = hashlib.sha256(trace_data.encode("utf-8")).hexdigest()
        sanitized_input = {"error_signature": trace.error_signature}
        oracle_data = json.dumps({"trace_hash": trace_hash, "input": sanitized_input}, sort_keys=True)
        oracle_hash = hashlib.sha256(oracle_data.encode("utf-8")).hexdigest()

        replay_oracle = ReplayOracle(
            trace_hash=trace_hash,
            sanitized_input=sanitized_input,
            expected_outcome={"status": "resolved"},
            oracle_hash=oracle_hash,
        )

        # Re-construct validated SkillSpec with trusted risk and oracle
        return SkillSpec(
            slug=spec.slug,
            description=spec.description,
            triggers=spec.triggers,
            non_triggers=spec.non_triggers,
            non_goals=spec.non_goals,
            tools=spec.tools,
            replay_oracle=replay_oracle,
            risk_assessment=trusted_risk,
            compatibility=spec.compatibility,
            license=spec.license,
        )
