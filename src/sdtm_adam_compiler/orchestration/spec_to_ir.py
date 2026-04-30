import uuid
import re

from sdtm_adam_compiler.parsers.spec_parser import load_spec_csv
from sdtm_adam_compiler.schemas.ir_schema import CompilerIR, DatasetPlan, DerivationRule, VariableRule


def _logic_to_derivation(logic: str, row: dict) -> DerivationRule:
    raw_logic = logic or ""
    text = raw_logic.lower()
    if text.startswith("hardcode"):
        expr = re.sub(r"(?i)^hardcode\s*", "", raw_logic).strip() or "''"
        return DerivationRule(kind="hardcode", expression=expr, sources=[])
    if "severity grade" in text and "aesev" in text:
        return DerivationRule(kind="derive", expression="severity_grade_from_aesev", sources=["AESEV"])
    if "inclusive days" in text and "aestdtc" in text and "aeendtc" in text:
        return DerivationRule(kind="date_transform", expression="inclusive_duration_days", sources=["AESTDTC", "AEENDTC"])
    if "aesdth" in text and "aeser" in text and "aesev" in text:
        return DerivationRule(kind="conditional", expression="serious_severe_death_flag", sources=["AESER", "AESEV"])
    if "uppercase" in text and "aeterm" in text:
        return DerivationRule(kind="derive", expression="uppercase_term", sources=["AETERM"])
    m = re.search(r"(?i)\bmap\s+(.+?)\s+to\s+", raw_logic)
    if m:
        src = m.group(1).strip()
        return DerivationRule(kind="direct_map", expression="", sources=[src])
    return DerivationRule(kind="direct_map", expression="", sources=[row["variable"]])


def build_ir_from_spec(spec_path: str, spec_type: str) -> CompilerIR:
    rows = load_spec_csv(spec_path)
    by_target: dict[str, list[dict]] = {}
    for r in rows:
        by_target.setdefault(r["target"], []).append(r)

    plans: list[DatasetPlan] = []
    for target, trows in by_target.items():
        source_datasets = sorted({r["source"] for r in trows if r["source"]})
        vars_out: list[VariableRule] = []
        for r in trows:
            length_val = int(r["length"]) if (r.get("length") or "").isdigit() else None
            vars_out.append(
                VariableRule(
                    target_variable=r["variable"],
                    source_dataset=r.get("source", ""),
                    label=r.get("label", ""),
                    target_type=r.get("type", ""),
                    length=length_val,
                    derivation=_logic_to_derivation(r.get("logic", ""), r),
                )
            )
        plans.append(DatasetPlan(dataset_name=target, source_datasets=source_datasets, variable_rules=vars_out))

    return CompilerIR(run_id=str(uuid.uuid4()), spec_type=spec_type, dataset_plans=plans)
