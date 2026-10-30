"""Windows filesystem path normalization utility."""

WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def normalize_windows_path(path_str: str) -> str:
    """Normalizes backslashes to forward slashes and sanitizes reserved names."""
    clean = path_str.replace("\\", "/")
    parts = clean.split("/")
    sanitized: list[str] = []
    for p in parts:
        stem = p.split(".")[0].upper()
        if stem in WINDOWS_RESERVED:
            sanitized.append(f"safe_{p}")
        else:
            sanitized.append(p)
    return "/".join(sanitized)
