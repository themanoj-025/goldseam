# Example 5: Human Correction Learning

## Overview
Demonstrates synthesizing a rule guideline from a human code correction diff using `goldseam learn`.

## Diff File
`examples/05_human_diff_correction/patch.diff`:
```diff
--- a/config/settings.py
+++ b/config/settings.py
@@ -10,3 +10,3 @@
-TIMEOUT = 5
+TIMEOUT = 30  # Increased for slow external APIs
```

## Running this example
```bash
goldseam learn --from-diff examples/05_human_diff_correction/patch.diff --why "Prevent timeout drops on slow external APIs"
```
Output:
Synthesizes a `RULE_ONLY` procedural record without introducing unneeded executable skills.
