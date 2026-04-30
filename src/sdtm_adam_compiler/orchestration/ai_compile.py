from dataclasses import asdict

from sdtm_adam_compiler.llm_client import call_llm_json
from sdtm_adam_compiler.orchestration.compiler import compile_ir
from sdtm_adam_compiler.orchestration.ir_convert import dict_to_ir
from sdtm_adam_compiler.orchestration.prompts import IR_SYSTEM_PROMPT, build_ir_user_prompt
from sdtm_adam_compiler.orchestration.repair import repair_ir_with_llm
from sdtm_adam_compiler.orchestration.spec_to_ir import build_ir_from_spec
from sdtm_adam_compiler.parsers.spec_parser import load_spec_csv


def run_compile_pipeline(
    *,
    spec_path: str,
    spec_type: str,
    standards_version: str,
    mode: str,
    provider: str,
    model: str,
    api_key: str,
    parse_temperature: float,
    compile_temperature: float,
    repair_temperature: float,
    repair_retries: int,
) -> tuple[object, dict]:
    diagnostics: dict = {
        "mode": mode,
        "llm_used": False,
        "repair_attempts": 0,
        "fallback_used": False,
        "errors": [],
    }

    det_ir = build_ir_from_spec(spec_path, spec_type)
    det_result = compile_ir(det_ir, standards_version=standards_version)

    if mode == "deterministic":
        diagnostics["fallback_used"] = False
        return det_ir, {**det_result, "diagnostics": diagnostics}

    # LLM or consensus path
    try:
        rows = load_spec_csv(spec_path)
        payload = call_llm_json(
            provider=provider,
            model=model,
            api_key=api_key,
            system_prompt=IR_SYSTEM_PROMPT,
            user_prompt=build_ir_user_prompt(spec_type, standards_version, rows),
            temperature=compile_temperature if mode == "llm" else parse_temperature,
        )
        diagnostics["llm_used"] = True
        llm_ir = dict_to_ir(payload, spec_type_fallback=spec_type)
        llm_result = compile_ir(llm_ir, standards_version=standards_version)
        all_issues = (llm_result.get("schema_issues") or []) + (llm_result.get("semantic_issues") or [])

        ir_work = llm_ir
        result_work = llm_result
        retries = 0
        while all_issues and retries < repair_retries:
            repaired_payload = repair_ir_with_llm(
                provider=provider,
                model=model,
                api_key=api_key,
                temperature=repair_temperature,
                issues=all_issues,
                ir_payload=asdict(ir_work),
            )
            ir_work = dict_to_ir(repaired_payload, spec_type_fallback=spec_type)
            result_work = compile_ir(ir_work, standards_version=standards_version)
            all_issues = (result_work.get("schema_issues") or []) + (result_work.get("semantic_issues") or [])
            retries += 1
            diagnostics["repair_attempts"] = retries

        if result_work.get("ok"):
            return ir_work, {**result_work, "diagnostics": diagnostics}

        diagnostics["fallback_used"] = True
        if mode == "consensus" and det_result.get("ok"):
            return det_ir, {**det_result, "diagnostics": diagnostics}
        return det_ir, {**det_result, "diagnostics": diagnostics}
    except Exception as e:
        diagnostics["errors"].append(str(e))
        diagnostics["fallback_used"] = True
        return det_ir, {**det_result, "diagnostics": diagnostics}

