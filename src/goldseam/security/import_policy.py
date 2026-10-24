"""Security policy loader, module import validator, and deterministic risk evaluator."""

import hashlib
import tomllib
from pathlib import Path

from goldseam.models.spec import RiskAssessment, RiskLevel, SideEffect


class SecurityPolicy:
    def __init__(self, policy_dict: dict[str, object], raw_content: str) -> None:
        self.raw_content = raw_content
        self.policy_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        self.presets: dict[str, dict[str, object]] = policy_dict.get("presets", {})  # type: ignore[assignment]
        self.forbidden: dict[str, list[str]] = policy_dict.get("forbidden", {})  # type: ignore[assignment]
        self.forbidden_calls = set(self.forbidden.get("calls", []))
        self.forbidden_attributes = set(self.forbidden.get("attributes", []))
        self.forbidden_modules = set(self.forbidden.get("modules", []))

    @classmethod
    def load_default(cls, policy_path: Path | None = None) -> "SecurityPolicy":
        path = policy_path or (Path(__file__).parent / "policy.toml")
        with open(path, "rb") as f:
            raw_bytes = f.read()
        raw_text = raw_bytes.decode("utf-8")
        data = tomllib.loads(raw_text)
        return cls(data, raw_text)

    def is_module_allowed(self, module_name: str, preset: str = "strict") -> bool:
        """Checks if a module (or top-level package) is allowed under the given preset."""
        top_pkg = module_name.split(".")[0]

        # Allow local bundle package imports (e.g. from scripts.normalizer import ...)
        if top_pkg in ("scripts", "tests"):
            return True

        # Explicitly forbidden modules are blocked unconditionally
        if top_pkg in self.forbidden_modules or module_name in self.forbidden_modules:
            return False

        preset_data = self.presets.get(preset)
        if not preset_data:
            return False

        allowed = preset_data.get("allowed_modules", [])
        if isinstance(allowed, (list, set, tuple)):
            return (top_pkg in allowed) or (module_name in allowed)
        return False

    def evaluate_risk(
        self,
        declared_side_effects: list[SideEffect],
        imported_modules: list[str],
        preset: str = "strict",
    ) -> RiskAssessment:
        """
        Deterministically assesses security risk level based on declared capabilities and AST imports.
        Does NOT rely on LLM self-reported risk.
        """
        flagged_imports: list[str] = []
        for mod in imported_modules:
            if not self.is_module_allowed(mod, preset):
                flagged_imports.append(mod)

        # Critical: Network side effect or forbidden modules
        if SideEffect.NETWORK in declared_side_effects:
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                justification="Network access declared or requested by capability.",
                evaluated_by="policy:deterministic_v1",
                declared_side_effects=declared_side_effects,
                flagged_imports=flagged_imports,
            )

        # Critical: Blocked forbidden modules
        if any(m.split(".")[0] in self.forbidden_modules for m in imported_modules):
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                justification=f"Strictly forbidden system/introspection module imported: {flagged_imports}",
                evaluated_by="policy:deterministic_v1",
                declared_side_effects=declared_side_effects,
                flagged_imports=flagged_imports,
            )

        # High: Workspace writing or unapproved module imports
        if SideEffect.WRITE_WORKSPACE in declared_side_effects or flagged_imports:
            reasons: list[str] = []
            if SideEffect.WRITE_WORKSPACE in declared_side_effects:
                reasons.append("Modifies workspace filesystem.")
            if flagged_imports:
                reasons.append(f"Imports outside '{preset}' allowlist: {flagged_imports}")
            return RiskAssessment(
                level=RiskLevel.HIGH,
                justification="; ".join(reasons),
                evaluated_by="policy:deterministic_v1",
                declared_side_effects=declared_side_effects,
                flagged_imports=flagged_imports,
            )

        # Medium: Workspace read
        if SideEffect.READ_WORKSPACE in declared_side_effects:
            return RiskAssessment(
                level=RiskLevel.MEDIUM,
                justification="Reads workspace filesystem without modification.",
                evaluated_by="policy:deterministic_v1",
                declared_side_effects=declared_side_effects,
                flagged_imports=[],
            )

        # Low: Pure computation without side-effects using approved modules
        return RiskAssessment(
            level=RiskLevel.LOW,
            justification="Pure deterministic computation with no workspace side-effects and allowed imports.",
            evaluated_by="policy:deterministic_v1",
            declared_side_effects=declared_side_effects,
            flagged_imports=[],
        )
