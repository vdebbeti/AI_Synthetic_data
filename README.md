# SDTM/ADaM Spec Compiler Blueprint

This folder contains a blueprint and starter scaffold for a robust AI-assisted SDTM/ADaM code generation tool.

## Goals
- Parse mapping specs into a normalized intermediate representation (IR).
- Validate IR with rule packs (schema + domain semantics).
- Auto-repair invalid IR with bounded retries.
- Fall back to deterministic assembly when needed.
- Render both SAS and R from one shared IR.
- Evaluate with golden cases (raw input + expected SDTM/ADaM outputs).

## Included Assets
- Architecture and roadmap: `docs/BLUEPRINT.md`
- Python package scaffold: `src/sdtm_adam_compiler/`
- Synthetic CDASH-style raw data: `data/raw/`
- Mapping specs: `data/specs/`
- Expected SDTM/ADaM outputs: `data/expected/`
- Golden case descriptors: `data/golden_cases/`
- SAS data build script: `scripts/build_sas_datasets.sas`
- Versioned standards profiles: `standards/sdtmig/*` and `standards/adamig/*`

## Quick Start
1. Review `docs/BLUEPRINT.md`.
2. Use `data/golden_cases/case_dm_ae_adsl_adae_v1.json` for first end-to-end tests.
3. Implement parser and validators in `src/sdtm_adam_compiler/`.
4. Compare generated outputs against `data/expected/*.csv`.

## Current Runnable Commands
- Print example IR (from SDTM spec):
  - `python -m scripts.bootstrap_ir_example`
- Run golden case evaluation:
  - `python -c "import sys,json; sys.path.insert(0,'src'); from sdtm_adam_compiler.eval.runner import run_case; print(json.dumps(run_case('data/golden_cases/case_dm_ae_adsl_adae_v1.json'), indent=2))"`

The eval currently executes deterministic spec compilation over CSV raw inputs, then diffs against expected SDTM/ADaM outputs.

## Streamlit App
- Install deps:
  - `pip install -r requirements.txt`
- Run app:
  - `streamlit run app.py`

The app includes:
- Standard-specific IG version selector (`SDTMIG` for SDTM, `ADaMIG` for ADaM)
- Routing modes (`deterministic`, `llm`, `consensus`)
- Sidebar OpenAI model/API key/temperature controls for LLM modes
- Upload spec CSV
- A standard-specific workflow/schema guide
- Standard-specific sample spec download
- Generated SAS and R code download buttons
- Eval tab to run scoped golden cases and inspect per-dataset mismatch details
- Session event log with sidebar download

Mode behavior:
- `deterministic`: no LLM calls; uses parser + validators only.
- `llm`: attempts LLM IR generation, then repair loop, then falls back to deterministic on failure.
- `consensus`: same as `llm`, but explicitly designed to keep deterministic fallback as safety baseline.
- LLM modes currently support OpenAI only.

Execution eval behavior:
- Eval compares deterministic compiled outputs to expected golden datasets.
- Eval is scoped by standard and dataset, so an SDTM AE check reports only AE instead of every domain in the golden case.
- Eval does not execute generated SAS/R code. Generated code should be reviewed and run in the user's controlled SAS/R environment.
