# 90-Second Product Demo Script

**Host / Screen:** Terminal with Goldseam CLI installed.

---

### [00:00 - 00:15] The Hook
*(Screen shows raw agent terminal error: `ValueError: Extra data: line 1 column 15`)*  
**Voiceover:** "When your autonomous agents crash on unbracketed JSON or malformed input, what happens? They retry, fail, or hallucinate. Watch how Goldseam fixes this permanently."

---

### [00:15 - 00:40] The Compilation Command
*(Runs command)*
```bash
goldseam build --from-log failure.log --dry-run
```
*(Fast visual progress ticks: INGEST -> REDACT -> TRIAGE -> SPEC -> GENERATE -> STATIC_GATE -> TESTGEN)*  
**Voiceover:** "Goldseam redacts credentials, flags prompt injection attacks, triages the error into a typed SkillSpec, writes the Python tool, and authors independent regression tests."

---

### [00:40 - 01:10] The Sandbox & Installation
*(Runs command)*
```bash
goldseam review run-latest
```
*(Diff shown on screen with green additions)*  
**Voiceover:** "The tool is tested in an isolated sandbox with rootless permissions. We approve it, and Goldseam atomically installs it into our library, signing the files with cryptographic provenance."

---

### [01:10 - 01:30] Tamper Detection & Wrap-Up
*(Modifies 1 byte in the script, runs)*
```bash
goldseam verify ~/.goldseam/skills/json-stream-parser
```
*(Screen shows red alert: `TAMPER DETECTED / Integrity mismatch in scripts/tool.py`)*  
**Voiceover:** "Modify even a single byte, and Goldseam's provenance verification catches it immediately. Goldseam: making agentic AI deterministic, tested, and secure. Open source today on GitHub."
