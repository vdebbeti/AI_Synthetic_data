import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_profile(spec_type: str, version: str) -> dict:
    base = _repo_root() / "standards"
    if spec_type == "SDTM":
        p = base / "sdtmig" / version / "profile.json"
    elif spec_type == "ADaM":
        p = base / "adamig" / version / "profile.json"
    else:
        raise ValueError(f"Unknown spec_type: {spec_type}")
    if not p.exists():
        raise FileNotFoundError(f"Standards profile not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))

