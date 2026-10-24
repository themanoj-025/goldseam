# Example 3: Windows Path Normalizer

## Overview
Normalizes mixed forward/backward slashes, handles drive letter prefixes, and strips or rejects Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1..9`, `LPT1..9`).

## Running this example
```bash
goldseam build --from-log examples/03_windows_path_normalizer/input_trace.log --dry-run
```
