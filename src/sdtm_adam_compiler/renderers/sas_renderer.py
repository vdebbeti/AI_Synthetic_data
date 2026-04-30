from sdtm_adam_compiler.schemas.ir_schema import CompilerIR


def render_sas(ir: CompilerIR) -> str:
    lines = [
        "/* Auto-generated SAS program from CompilerIR */",
        f"/* Spec Type: {ir.spec_type} */",
    ]
    for ds in ir.dataset_plans:
        lines.append("")
        lines.append(f"/* Dataset: {ds.dataset_name} */")
        lines.append(f"data {ds.dataset_name.lower()};")
        src = ds.source_datasets[0].lower() if ds.source_datasets else "source_ds"
        lines.append(f"  set {src};")
        for vr in ds.variable_rules:
            if vr.derivation and vr.derivation.kind == "hardcode":
                lines.append(f"  {vr.target_variable} = {vr.derivation.expression};")
            elif vr.derivation and vr.derivation.kind == "direct_map" and vr.derivation.sources:
                lines.append(f"  {vr.target_variable} = {vr.derivation.sources[0]};")
        lines.append("run;")
    return "\n".join(lines)

