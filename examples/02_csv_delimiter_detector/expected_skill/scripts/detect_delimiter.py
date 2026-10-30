"""CSV delimiter detection utility."""


def detect_delimiter(sample_text: str) -> str:
    """Detects field delimiter character from tabular text samples."""
    candidates = [",", "\t", ";", "|"]
    lines = [line.strip() for line in sample_text.splitlines() if line.strip()][:10]
    if not lines:
        return ","

    scores: dict[str, int] = {c: 0 for c in candidates}
    for delim in candidates:
        counts = [line.count(delim) for line in lines]
        if counts and all(c > 0 and c == counts[0] for c in counts):
            scores[delim] += 10 + counts[0]
        else:
            scores[delim] += sum(counts)

    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else ","
