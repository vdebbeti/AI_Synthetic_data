import uuid

from sdtm_adam_compiler.schemas.ir_schema import CompilerIR
from sdtm_adam_compiler.standards.profile_loader import load_profile
from sdtm_adam_compiler.validators.schema_validator import validate_ir_schema
from sdtm_adam_compiler.validators.semantic_validator import validate_semantics


def compile_ir(ir: CompilerIR, standards_version: str | None = None) -> dict:
    schema_issues = validate_ir_schema(ir)
    profile = load_profile(ir.spec_type, standards_version) if standards_version else None
    semantic_issues = validate_semantics(ir, profile=profile)
    warnings: list[dict] = []
    baseline = "3.3" if ir.spec_type == "SDTM" else "1.2"
    if standards_version and standards_version != baseline:
        warnings.append(
            {
                "code": "standards.version_delta",
                "message": f"Using {ir.spec_type} IG {standards_version} instead of baseline {baseline}. Review version-specific deltas.",
            }
        )
    if profile and profile.get("notes"):
        for note in profile["notes"]:
            warnings.append({"code": "standards.profile_note", "message": str(note)})
    return {
        "run_id": ir.run_id or str(uuid.uuid4()),
        "standards_version": standards_version,
        "schema_issues": schema_issues,
        "semantic_issues": semantic_issues,
        "warnings": warnings,
        "ok": not schema_issues and not semantic_issues,
    }
