"""Capability router evaluating diagnostic findings and routing to pipeline targets."""

from goldseam.models.diagnosis import Diagnosis, Route


class CapabilityRouter:
    def route(self, diagnosis: Diagnosis) -> tuple[Route, str]:
        """
        Determines the appropriate pipeline route based on diagnostic evidence.
        Returns (Route, rationale).
        """
        # Low confidence -> discard to avoid synthesizing unverified capabilities
        if diagnosis.confidence < 0.5:
            return Route.DISCARD, f"Confidence score ({diagnosis.confidence:.2f}) below threshold 0.50; discarded."

        # Model recommended DISCARD
        if diagnosis.recommended_route == Route.DISCARD:
            return Route.DISCARD, diagnosis.rationale

        # Model recommended RULE_ONLY for behavioral / stylistic guidance
        if diagnosis.recommended_route == Route.RULE_ONLY:
            return Route.RULE_ONLY, diagnosis.rationale

        # SCRIPT vs MCP_TOOL vs SKILL
        if diagnosis.recommended_route in (Route.SCRIPT, Route.MCP_TOOL, Route.SKILL):
            return diagnosis.recommended_route, diagnosis.rationale

        # Default fallback
        return Route.SKILL, "Defaulting to full Agent Skill pipeline."
