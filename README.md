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
- IG version selectors (`SDTMIG` and `ADaMIG`)
- Routing modes (`deterministic`, `llm`, `consensus`)
- Sidebar controls for provider/model/API key and temperatures
- Upload spec CSV
- `Download sample SDTM spec` button
- `Download sample ADaM spec` button
- Generated SAS and R code download buttons
- Eval tab to run golden cases and inspect per-dataset mismatch details
- Eval mode toggle: `data_only` vs `execute_generated_code`
- Session event log with sidebar download

Mode behavior:
- `deterministic`: no LLM calls; uses parser + validators only.
- `llm`: attempts LLM IR generation, then repair loop, then falls back to deterministic on failure.
- `consensus`: same as `llm`, but explicitly designed to keep deterministic fallback as safety baseline.

Execution eval behavior:
- `data_only`: compares deterministic compiled outputs to expected golden datasets.
- `execute_generated_code`: also attempts to run generated SAS/R code and reports runtime status/logs.
  - If SAS or R runtimes are not installed on host, execution is marked `skipped` with reason.
  - You can provide explicit runtime paths in the app sidebar (`SAS executable path`, `Rscript path`).
