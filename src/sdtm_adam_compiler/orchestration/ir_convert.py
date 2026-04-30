from sdtm_adam_compiler.schemas.ir_schema import CompilerIR, DatasetPlan, DerivationRule, VariableRule


def dict_to_ir(payload: dict, spec_type_fallback: str) -> CompilerIR:
    plans: list[DatasetPlan] = []
    for ds in payload.get("dataset_plans", []) or []:
        vars_out: list[VariableRule] = []
        for vr in ds.get("variable_rules", []) or []:
            d = vr.get("derivation") or {}
            deriv = DerivationRule(
                kind=d.get("kind", "direct_map"),
                expression=d.get("expression", ""),
                sources=list(d.get("sources", []) or []),
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

