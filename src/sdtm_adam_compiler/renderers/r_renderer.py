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
        lines.append(",\n".join(assigns) if assigns else "    .keep = 'all'")
        lines.append("  )")
    return "\n".join(lines)

