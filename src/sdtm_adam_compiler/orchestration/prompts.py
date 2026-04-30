IR_SYSTEM_PROMPT = """
You are a senior clinical programming architect.
Return ONLY one valid JSON object that matches the target IR shape.
No prose, no markdown, no comments.
"""


def build_ir_user_prompt(spec_type: str, standards_version: str, spec_rows: list[dict]) -> str:
    return f"""
Build a CompilerIR JSON for {spec_type} using IG version {standards_version}.

Required JSON shape:
{{
  "run_id": "<uuid-or-string>",
  "spec_type": "{spec_type}",
  "dataset_plans": [
    {{
      "dataset_name": "DM",
      "source_datasets": ["raw_dm"],
      "keys": [],
      "variable_rules": [
        {{
          "target_variable": "STUDYID",
          "source_dataset": "raw_dm",
          "label": "Study Identifier",
          "target_type": "char",
          "length": 20,
          "derivation": {{
            "kind": "direct_map",
            "expression": "",
            "sources": ["STUDYID"]
          }},
          "codelist": []
        }}
      ]
    }}
  ],
  "metadata": {{}}
}}

Rules:
- Use exact target/source variable names from rows.
- For logic with "Hardcode", set derivation.kind="hardcode" and expression as literal.
- For direct map and map-to patterns, use derivation.kind="direct_map" with sources.
- Keep source_dataset populated for each variable rule.
- Hardcode string literals MUST be quoted, for example `'AE'` and `'Y'`.
- Do not emit free-text pseudo-code in derivation.expression.
- For AE common derivations, use these exact canonical mappings:
  - `AEDECOD` from `AETERM`: `kind="derive"`, `expression="uppercase_term"`, `sources=["AETERM"]`
  - `AEDUR` from `AESTDTC` and `AEENDTC`: `kind="date_transform"`, `expression="inclusive_duration_days"`, `sources=["AESTDTC","AEENDTC"]`
  - `AETOXGR` from `AESEV`: `kind="derive"`, `expression="severity_grade_from_aesev"`, `sources=["AESEV"]`
  - `AESDTH` from `AESER` and `AESEV`: `kind="conditional"`, `expression="serious_severe_death_flag"`, `sources=["AESER","AESEV"]`

Spec rows:
{spec_rows}
"""


REPAIR_SYSTEM_PROMPT = """
You repair invalid CompilerIR JSON.
Return ONLY corrected JSON object. No prose.
"""


def build_repair_user_prompt(ir_payload: dict, issues: list[dict]) -> str:
    return f"""
Fix this IR JSON using the validation issues.

Validation issues:
{issues}

IR JSON:
{ir_payload}
"""
