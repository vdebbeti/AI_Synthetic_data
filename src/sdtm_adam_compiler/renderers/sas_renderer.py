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
            elif vr.derivation and vr.derivation.expression == "severity_grade_from_aesev":
                lines.append(f"  if AESEV = 'MILD' then {vr.target_variable} = 1;")
                lines.append(f"  else if AESEV = 'MODERATE' then {vr.target_variable} = 2;")
                lines.append(f"  else if AESEV = 'SEVERE' then {vr.target_variable} = 3;")
            elif vr.derivation and vr.derivation.expression == "inclusive_duration_days":
                lines.append(f"  {vr.target_variable} = input(AEENDTC, yymmdd10.) - input(AESTDTC, yymmdd10.) + 1;")
            elif vr.derivation and vr.derivation.expression == "serious_severe_death_flag":
                lines.append(f"  if AESER = 'Y' and AESEV = 'SEVERE' then {vr.target_variable} = 'Y';")
                lines.append(f"  else {vr.target_variable} = 'N';")
            elif vr.derivation and vr.derivation.expression == "uppercase_term":
                lines.append(f"  {vr.target_variable} = upcase(AETERM);")
        lines.append("run;")
    return "\n".join(lines)
