# SDTM/ADaM AI Compiler Blueprint (v1)

## 1. Recommended System Shape
Use a compiler-style pipeline:

1) Spec Parse  
2) Normalized IR Build  
3) Guardrail Validation  
4) Auto-Repair (bounded)  
5) Deterministic Fallback  
6) Dual Renderer (SAS + R)  
7) Eval Harness + Golden Cases

This avoids brittle one-shot prompt-to-code behavior.

## 2. Core Modules

### `parsers/`
- `spec_parser.py`: parse Excel/CSV spec into row model.
- `cdash_reference.py`: query CDASH reference columns from `CDASHIG_v2.3.csv`.

### `schemas/`
- `ir_schema.py`: dataclasses/pydantic models for:
  - `StudyContext`
  - `DatasetPlan`
  - `VariableRule`
  - `DerivationRule`
  - `TraceabilityLink`
  - `CompilerIR`

### `validators/`
- `schema_validator.py`: structural checks.
- `semantic_validator.py`: SDTM/ADaM rule checks.
- `domain_rules.py`: domain-specific expectations.

### `orchestration/`
- `compiler.py`: run parse -> validate -> repair -> fallback -> render.
- `repair.py`: LLM JSON repair interface with retry policy.
- `fallback.py`: deterministic minimal-safe compiler rules.

### `renderers/`
- `sas_renderer.py`: DATA step / PROC SQL templates.
- `r_renderer.py`: dplyr/tidyr templates.

### `eval/`
- `runner.py`: execute golden suite and compute metrics.
- `metrics.py`: pass rate, rule-violation counts, fallback rate.

## 3. Intermediate Representation (IR)
IR is language-neutral and auditable.

Top-level fields:
- `run_id`
- `spec_type` (`SDTM` or `ADaM`)
- `study_context`
- `dataset_plans[]`
- `global_filters[]`
- `traceability[]`
- `metadata` (model, temperature, timestamps)

Per `dataset_plan`:
- `dataset_name`
- `source_datasets[]`
- `keys[]`
- `variable_rules[]` with:
  - `target_variable`
  - `target_type`
  - `length`
  - `label`
  - `derivation` (direct_map/hardcode/conditional/derive/date)
  - `sources[]`
  - `ct_rules[]`
- `checks[]` (post-derivation checks)

## 4. Guardrails to Reuse from TLF Tool Pattern
- Distinct parse/recipe/repair temperatures.
- Structured issue codes with path and severity.
- Auto-repair loop (max retries, e.g. 2).
- Deterministic fallback if repaired IR still invalid.
- Session/event logging and eval harness.

## 5. Initial Rule Packs

### SDTM v1 Rules
- Ensure presence of key identifiers in DM (`STUDYID`, `USUBJID`, `SUBJID`).
- Ensure `DOMAIN` constant equals dataset name where required.
- Ensure ISO8601 date/time outputs for `--DTC`.
- Ensure AE has `AETERM`, `AESTDTC` when source supports.

### ADaM v1 Rules
- ADSL key presence (`STUDYID`, `USUBJID`, treatment vars as available).
- Traceability references to SDTM source (`SRCVAR`, `SRCDOM` style metadata in IR).
- Flag discipline (`Y/N` for population flags).
- Numeric consistency for analysis variables.

## 6. Model and Temperature Policy
- Parse stage: `0.4-0.7`
- IR generation stage: `0.1-0.3`
- Repair stage: `0.0-0.1`
- Deterministic fallback: temperature-independent (non-LLM)

## 7. Golden Case Design
Each golden case includes:
- Raw input datasets (CSV + optional SAS import script)
- Spec rows
- Expected SDTM outputs
- Expected ADaM outputs
- Assertion rules and tolerance policy

## 8. Metrics
- `case_pass_rate`
- `validator_issue_count`
- `repair_retry_count`
- `fallback_rate`
- `column_level_match_rate`
- `row_level_exact_match_rate`

## 9. Deployment Recommendation
- Python package is source of truth.
- Streamlit as rapid internal workbench.
- Website calls Python API for production UX.
- Same eval harness gates both environments.

## 10. v1 Build Milestones
1. Complete IR schema + parser.  
2. Implement SDTM DM/AE and ADaM ADSL/ADAE rule packs.  
3. SAS + R renderers for covered datasets.  
4. Wire eval harness to golden cases in `data/golden_cases/`.  
5. Add CI checks for deterministic regression.

