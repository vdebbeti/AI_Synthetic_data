import csv
from pathlib import Path


def load_cdash_reference(path: str | Path) -> list[dict]:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def get_domain_variables(cdash_rows: list[dict], domain: str) -> list[str]:
    d = domain.upper().strip()
    out = []
    for row in cdash_rows:
        if (row.get("Domain") or "").upper().strip() == d:
            var = (row.get("CDASHIG Variable") or "").strip().upper()
            if var:
                out.append(var)
    return sorted(set(out))

