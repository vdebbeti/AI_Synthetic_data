from sdtm_adam_compiler.schemas.ir_schema import CompilerIR, DatasetPlan, DerivationRule, VariableRule


def _is_quoted(text: str) -> bool:
    s = (text or "").strip()
    return len(s) >= 2 and ((s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"'))


def _looks_numeric(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if s.replace(".", "", 1).isdigit():
        return True
    return False


def _normalize_hardcode(vr: dict, expression: str) -> str:
    expr = (expression or "").strip()
    if not expr:
        return "''"
    target_type = (vr.get("target_type") or "").strip().lower()
    if target_type == "char" and not _is_quoted(expr) and not _looks_numeric(expr):
        return f"'{expr}'"
    return expr


def _normalize_llm_derivation(vr: dict, kind: str, expression: str, sources: list[str]) -> tuple[str, str, list[str]]:
    target = (vr.get("target_variable") or "").upper()
    expr = (expression or "").strip()
    expr_l = expr.lower()
    srcs = [str(s) for s in (sources or []) if str(s).strip()]
    srcs_upper = {s.upper() for s in srcs}

    if target == "AEDECOD" and ("upper" in expr_l or ("AETERM" in srcs_upper and kind in {"derive", "direct_map"})):
        return "derive", "uppercase_term", ["AETERM"]
    if target == "AEDUR" and ({"AESTDTC", "AEENDTC"} <= srcs_upper or ("days" in expr_l and "aestdtc" in expr_l and "aeendtc" in expr_l)):
        return "date_transform", "inclusive_duration_days", ["AESTDTC", "AEENDTC"]
    if target == "AETOXGR" and ("aesev" in expr_l or "grade" in expr_l or "AESEV" in srcs_upper):
        return "derive", "severity_grade_from_aesev", ["AESEV"]
    if target == "AESDTH" and (
        "when" in expr_l
        or ("aeser" in expr_l and "aesev" in expr_l)
        or {"AESER", "AESEV"} <= srcs_upper
    ):
        return "conditional", "serious_severe_death_flag", ["AESER", "AESEV"]

    return kind, expr, srcs


def dict_to_ir(payload: dict, spec_type_fallback: str) -> CompilerIR:
    plans: list[DatasetPlan] = []
    for ds in payload.get("dataset_plans", []) or []:
        vars_out: list[VariableRule] = []
        for vr in ds.get("variable_rules", []) or []:
            d = vr.get("derivation") or {}
            kind = d.get("kind", "direct_map")
            expression = d.get("expression", "")
            sources = list(d.get("sources", []) or [])
            kind, expression, sources = _normalize_llm_derivation(vr, kind, expression, sources)
            if kind == "hardcode":
                expression = _normalize_hardcode(vr, expression)
            deriv = DerivationRule(
                kind=kind,
                expression=expression,
                sources=sources,
            )
            vars_out.append(
                VariableRule(
                    target_variable=vr.get("target_variable", ""),
                    source_dataset=vr.get("source_dataset", ""),
                    label=vr.get("label", ""),
                    target_type=vr.get("target_type", ""),
                    length=vr.get("length"),
                    derivation=deriv,
                    codelist=list(vr.get("codelist", []) or []),
                )
            )
        plans.append(
            DatasetPlan(
                dataset_name=ds.get("dataset_name", ""),
                source_datasets=list(ds.get("source_datasets", []) or []),
                keys=list(ds.get("keys", []) or []),
                variable_rules=vars_out,
            )
        )
    return CompilerIR(
        run_id=payload.get("run_id", ""),
        spec_type=payload.get("spec_type", spec_type_fallback),
        dataset_plans=plans,
        metadata=payload.get("metadata", {}) or {},
    )
