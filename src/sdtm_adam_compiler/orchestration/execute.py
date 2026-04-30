import csv
from collections import Counter
from pathlib import Path

from sdtm_adam_compiler.schemas.ir_schema import CompilerIR, DatasetPlan, VariableRule


def _load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _parse_hardcode(expr: str) -> str:
    text = (expr or "").strip()
    if len(text) >= 2 and ((text[0] == "'" and text[-1] == "'") or (text[0] == '"' and text[-1] == '"')):
        return text[1:-1]
    return text


def _apply_var_rule(row: dict, rule: VariableRule) -> str:
    if not rule.derivation:
        return ""
    if rule.derivation.kind == "hardcode":
        return _parse_hardcode(rule.derivation.expression)
    if rule.derivation.sources:
        return row.get(rule.derivation.sources[0], "")
    return row.get(rule.target_variable, "")


def _index_by_key(rows: list[dict], key: str) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for r in rows:
        k = str(r.get(key, ""))
        if k:
            idx[k] = r
    return idx


def _choose_base_dataset(plan: DatasetPlan) -> str:
    freq = Counter(v.source_dataset for v in plan.variable_rules if v.source_dataset)
    if freq:
        return freq.most_common(1)[0][0]
    return plan.source_datasets[0] if plan.source_datasets else ""


def _compile_dataset(plan: DatasetPlan, source_registry: dict[str, list[dict]]) -> list[dict]:
    base_ds = _choose_base_dataset(plan)
    source_rows = source_registry.get(base_ds, [])
    join_indices = {
        ds: _index_by_key(rows, "USUBJID")
        for ds, rows in source_registry.items()
        if ds != base_ds and rows and "USUBJID" in rows[0]
    }
    out = []
    for src in source_rows:
        rec: dict[str, str] = {}
        usubjid = str(src.get("USUBJID", ""))
        for vr in plan.variable_rules:
            if vr.source_dataset and vr.source_dataset != base_ds:
                join_row = join_indices.get(vr.source_dataset, {}).get(usubjid, {})
                rec[vr.target_variable] = _apply_var_rule(join_row, vr)
            else:
                rec[vr.target_variable] = _apply_var_rule(src, vr)
        out.append(rec)
    return out


def execute_ir_to_rows(ir: CompilerIR, raw_registry: dict[str, list[dict]]) -> dict[str, list[dict]]:
    working = dict(raw_registry)
    outputs: dict[str, list[dict]] = {}
    for plan in ir.dataset_plans:
        compiled = _compile_dataset(plan, working)
        ds_name = plan.dataset_name.upper()
        outputs[ds_name] = compiled
        working[ds_name] = compiled
    return outputs


def build_raw_registry(raw_inputs: list[dict], root_dir: str | Path | None = None) -> dict[str, list[dict]]:
    base = Path(root_dir or ".")
    reg: dict[str, list[dict]] = {}
    for item in raw_inputs:
        ds = item["dataset"]
        p = Path(item["path"])
        full = p if p.is_absolute() else (base / p)
        reg[ds] = _load_csv(full)
    return reg
