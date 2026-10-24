"""Trigger evaluation measuring activation precision and recall against synthetic queries."""

from pydantic import BaseModel, ConfigDict

from goldseam.models.spec import SkillSpec


class TriggerEvalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


class TriggerEvaluator:
    def evaluate_triggers(
        self,
        spec: SkillSpec,
        positive_prompts: list[str],
        negative_prompts: list[str],
    ) -> TriggerEvalResult:
        """
        Evaluates trigger activation against positive and negative benchmark prompts.
        Matches if any trigger keyword is contained and no non-trigger keyword matches.
        """
        tp = 0
        fn = 0
        fp = 0

        triggers_lower = [t.lower() for t in spec.triggers]
        non_triggers_lower = [nt.lower() for nt in spec.non_triggers]

        def matches_skill(prompt: str) -> bool:
            p = prompt.lower()
            has_trigger = any(t in p for t in triggers_lower)
            has_non_trigger = any(nt in p for nt in non_triggers_lower)
            return has_trigger and not has_non_trigger

        # Test positive prompts (should activate)
        for prompt in positive_prompts:
            if matches_skill(prompt):
                tp += 1
            else:
                fn += 1

        # Test negative prompts (should NOT activate)
        for prompt in negative_prompts:
            if matches_skill(prompt):
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return TriggerEvalResult(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
        )
