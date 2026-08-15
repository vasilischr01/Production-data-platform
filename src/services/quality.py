def assess_quality(value: float, source: str, event_type: str) -> str:
    if not source.strip() or not event_type.strip():
        return "bad"
    if abs(value) > 1_000_000_000:
        return "bad"
    return "good"

def normalize_value(value: float) -> float:
    return value / (1.0 + abs(value))
