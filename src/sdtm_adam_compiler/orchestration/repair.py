from sdtm_adam_compiler.llm_client import call_llm_json
from sdtm_adam_compiler.orchestration.prompts import REPAIR_SYSTEM_PROMPT, build_repair_user_prompt


def repair_ir_with_llm(
    *,
    provider: str,
    model: str,
    api_key: str,
    temperature: float,
    issues: list[dict],
    ir_payload: dict,
) -> dict:
    return call_llm_json(
        provider=provider,
        model=model,
        api_key=api_key,
        system_prompt=REPAIR_SYSTEM_PROMPT,
        user_prompt=build_repair_user_prompt(ir_payload=ir_payload, issues=issues),
        temperature=temperature,
    )
