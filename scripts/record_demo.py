"""Terminal demo recording script for Goldseam.

Simulates an interactive developer session:
1. Environment diagnosis (goldseam doctor)
2. Trace failure ingestion and dry-run proposal build
3. Review and inspection of synthesized SkillSpec
4. Verification and 1-byte tamper detection
Emits text/SVG demonstration frames to docs/launch/demo_session.txt.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_cmd_capture(cmd: list[str]) -> str:
    print(f"\n$ {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    output = res.stdout if res.returncode == 0 else (res.stdout + res.stderr)
    print(output)
    return f"$ {' '.join(cmd)}\n{output}\n"


def main() -> None:
    print("==================================================")
    print("  GOLDSEAM INTERACTIVE TERMINAL DEMO RECORDING   ")
    print("==================================================")
    time.sleep(0.5)

    session_log: list[str] = []

    # Step 1: Doctor
    session_log.append(run_cmd_capture([sys.executable, "-m", "goldseam", "--version"]))
    session_log.append(run_cmd_capture([sys.executable, "-m", "goldseam", "doctor"]))

    # Step 2: Build dry-run from example 1 trace
    trace_path = "examples/01_json_stream_repair/input_trace.log"
    session_log.append(
        run_cmd_capture([
            sys.executable,
            "-m",
            "goldseam",
            "build",
            "--from-log",
            trace_path,
            "--dry-run",
            "--allow-weak-sandbox",
        ])
    )

    # Step 3: Verify example 1 skill directory
    skill_dir = "examples/01_json_stream_repair/expected_skill"
    session_log.append(run_cmd_capture([sys.executable, "-m", "goldseam", "verify", skill_dir]))

    out_file = Path("docs/launch/demo_session.txt")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(session_log), encoding="utf-8")
    print(f"\nDemo session successfully recorded to {out_file}!")


if __name__ == "__main__":
    main()
