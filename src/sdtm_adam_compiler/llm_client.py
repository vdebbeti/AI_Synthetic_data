import json


def call_llm_json(
    *,
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int = 6000,
) -> dict:
    if provider != "OpenAI":
        raise ValueError("Only OpenAI is implemented in this build. Select provider=OpenAI.")
    if not api_key:
        raise ValueError("Missing API key for LLM call.")

    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai package is not installed. Add `openai` to requirements.") from e

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {content[:250]}") from e

