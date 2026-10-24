# Goldseam Key Engineering Decisions

1. **Self-Contained Execution:** No external network dependence for core suites. Deterministic `FakeLLM` provides full replayable testing.
2. **Strict Separation of Concerns:**
   - `SkillSpec` defines contract.
   - `Generator` writes implementation.
   - `TestGen` writes tests purely from `SkillSpec` without seeing implementation.
   - `Sandbox` verifies code without host imports.
3. **No Dynamic Code Import:** The host orchestrator never executes `importlib.import_module` on generated skill scripts.
4. **Fail-Closed Container Policy:** If Docker is not reachable, untrusted code execution returns `BLOCKED`. Weak subprocess execution is restricted strictly to test fixtures under explicit `--allow-weak-sandbox`.
5. **Standard-Conformant Frontmatter:** `SKILL.md` uses only official Agent Skills fields (`name`, `description`, etc.). Extensions are kept in `goldseam.manifest.json`.
