from sdtm_adam_compiler.schemas.ir_schema import CompilerIR


def render_r(ir: CompilerIR) -> str:
    lines = [
        "# Auto-generated R program from CompilerIR",
        f"# Spec Type: {ir.spec_type}",
        "library(dplyr)",
    ]
    for ds in ir.dataset_plans:
        lines.append("")
        src = ds.source_datasets[0].lower() if ds.source_datasets else "source_ds"
        lines.append(f"{ds.dataset_name.lower()} <- {src} %>%")
        lines.append("  mutate(")
        assigns = []
        for vr in ds.variable_rules:
            if vr.derivation and vr.derivation.kind == "hardcode":
                assigns.append(f"    {vr.target_variable} = {vr.derivation.expression}")
            elif vr.derivation and vr.derivation.kind == "direct_map" and vr.derivation.sources:
                assigns.append(f"    {vr.target_variable} = {vr.derivation.sources[0]}")
            elif vr.derivation and vr.derivation.expression == "severity_grade_from_aesev":
                assigns.append(
                    f"    {vr.target_variable} = case_when(AESEV == 'MILD' ~ 1L, AESEV == 'MODERATE' ~ 2L, AESEV == 'SEVERE' ~ 3L, TRUE ~ NA_integer_)"
                )
            elif vr.derivation and vr.derivation.expression == "inclusive_duration_days":
                assigns.append(f"    {vr.target_variable} = as.integer(as.Date(AEENDTC) - as.Date(AESTDTC)) + 1L")
            elif vr.derivation and vr.derivation.expression == "serious_severe_death_flag":
                assigns.append(f"    {vr.target_variable} = if_else(AESER == 'Y' & AESEV == 'SEVERE', 'Y', 'N')")
            elif vr.derivation and vr.derivation.expression == "uppercase_term":
                assigns.append(f"    {vr.target_variable} = toupper(AETERM)")
        lines.append(",\n".join(assigns) if assigns else "    .keep = 'all'")
        lines.append("  )")
    return "\n".join(lines)
