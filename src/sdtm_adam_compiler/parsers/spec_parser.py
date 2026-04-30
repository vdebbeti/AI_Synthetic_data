import csv
from pathlib import Path


REQUIRED_COLUMNS = {"source", "target", "variable", "logic"}


def load_spec_csv(path: str | Path) -> list[dict]:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    normalized = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]
    cols = set(normalized[0].keys()) if normalized else set()
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(f"Missing required columns in spec: {sorted(missing)}")
    return normalized

