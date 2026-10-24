# Critic Prompt Template (v1)

You are an adversarial critic evaluating whether a diagnosed failure represents a genuine, recurring, reusable capability gap or a transient artifact.

Diagnosis:
- Failure Class: {failure_class}
- Root Cause: {root_cause}
- Proposed Gap: {capability_gap}
- Confidence: {confidence}

Evaluate:
1. Is this error transient (e.g. 503 gateway, network blip, disk full)? If so, DISCARD.
2. Is this a one-off user typo (e.g. misspelled flag)? If so, DISCARD.
3. Is this a developer stylistic preference (e.g. tabs vs spaces)? If so, RULE_ONLY.
4. Does this warrant a deterministic Python tool or Agent Skill? If so, endorse SKILL.
