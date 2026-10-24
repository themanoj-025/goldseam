---
name: windows-path-normalizer
description: Normalizes Windows filesystem paths and sanitizes reserved device names.
---

# windows-path-normalizer

## When to Use
- When operating in cross-platform environments handling Windows drive letters and backslashes.
- When validating paths before filesystem calls to prevent `Errno 22` on reserved device stems.

## When Not to Use
- When paths are pure web URLs or POSIX URIs.
