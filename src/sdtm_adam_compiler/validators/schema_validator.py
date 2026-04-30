from dataclasses import asdict

from sdtm_adam_compiler.schemas.ir_schema import CompilerIR


def validate_ir_schema(ir: CompilerIR) -> list[dict]:
    issues: list[dict] = []
    if ir.spec_type not in {"SDTM", "ADaM"}:
        issues.append({"code": "schema.spec_type", "path": "$.spec_type", "message": "spec_type must be SDTM or ADaM"})
    if not ir.dataset_plans:
        issues.append({"code": "schema.dataset_plans", "path": "$.dataset_plans", "message": "at least one dataset plan is required"})
    for i, ds in enumerate(ir.dataset_plans):
        if not ds.dataset_name:
            issues.append({"code": "schema.dataset_name", "path": f"$.dataset_plans[{i}].dataset_name", "message": "dataset_name is required"})
    _ = asdict(ir)
    return issues

