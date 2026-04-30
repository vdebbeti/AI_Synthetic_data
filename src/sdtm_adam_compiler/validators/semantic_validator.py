from sdtm_adam_compiler.schemas.ir_schema import CompilerIR
from sdtm_adam_compiler.validators.domain_rules import (
    ADAM_ADAE_REQUIRED,
    ADAM_ADSL_REQUIRED,
    SDTM_AE_REQUIRED,
    SDTM_DM_REQUIRED,
)


def validate_semantics(ir: CompilerIR, profile: dict | None = None) -> list[dict]:
    issues: list[dict] = []
    for i, ds in enumerate(ir.dataset_plans):
        vars_present = {v.target_variable.upper() for v in ds.variable_rules}
        name = ds.dataset_name.upper()
        required = set()
        if profile:
            ds_prof = ((profile.get("datasets") or {}).get(name) or {})
            required = set(ds_prof.get("required_variables") or [])
        else:
            if ir.spec_type == "SDTM" and name == "DM":
                required = SDTM_DM_REQUIRED
            elif ir.spec_type == "SDTM" and name == "AE":
                required = SDTM_AE_REQUIRED
            elif ir.spec_type == "ADaM" and name == "ADSL":
                required = ADAM_ADSL_REQUIRED
            elif ir.spec_type == "ADaM" and name == "ADAE":
                required = ADAM_ADAE_REQUIRED
        missing = sorted(required - vars_present)
        for m in missing:
            issues.append(
                {
                    "code": "semantics.required_var_missing",
                    "path": f"$.dataset_plans[{i}]",
                    "message": f"{name} missing required variable {m}",
                }
            )
    return issues
