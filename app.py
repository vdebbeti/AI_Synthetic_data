from pathlib import Path
import sys
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sdtm_adam_compiler.orchestration.ai_compile import run_compile_pipeline
from sdtm_adam_compiler.renderers.sas_renderer import render_sas
from sdtm_adam_compiler.renderers.r_renderer import render_r
from sdtm_adam_compiler.eval.runner import run_case
from sdtm_adam_compiler.parsers.spec_parser import load_spec_csv


SPEC_CONFIG = {
    "SDTM": {
        "ig_label": "SDTMIG Version",
        "versions": ["3.3", "3.4"],
        "sample_path": ROOT / "data" / "specs" / "sample_sdtm_spec.csv",
        "sample_name": "sample_sdtm_spec.csv",
        "source_note": "Use CDASH/raw source datasets as inputs.",
        "output_note": "Generates SDTM domain code such as DM, AE, LB, or VS.",
    },
    "ADaM": {
        "ig_label": "ADaMIG Version",
        "versions": ["1.2", "1.3"],
        "sample_path": ROOT / "data" / "specs" / "sample_adam_spec.csv",
        "sample_name": "sample_adam_spec.csv",
        "source_note": "Use SDTM datasets as inputs.",
        "output_note": "Generates ADaM analysis dataset code such as ADSL, ADAE, or ADLB.",
    },
}


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _render_workflow(spec_type: str) -> None:
    cfg = SPEC_CONFIG[spec_type]
    st.markdown("### User Workflow")
    steps = [
        ("1", "Choose standard", f"Select {spec_type} and the matching {cfg['ig_label']}."),
        ("2", "Prepare CSV spec", "Required columns: source, target, variable, logic. Optional: label, type, length."),
        ("3", "Generate code", "Click the primary Generate SAS and R Code button. This is the main app action."),
        ("4", "Review outputs", "Inspect validation results, IR, SAS, and R before downloading code."),
    ]
    cols = st.columns(4)
    for col, (num, title, body) in zip(cols, steps):
        with col:
            st.markdown(f"**{num}. {title}**")
            st.caption(body)
    st.info(f"{cfg['source_note']} {cfg['output_note']}")


def _case_dataset_options(case_path: Path, spec_type: str) -> list[str]:
    case = json.loads(case_path.read_text(encoding="utf-8"))
    root = case_path.parents[2] if len(case_path.parents) >= 3 else ROOT
    expected = {e["dataset"].upper() for e in case.get("expected_outputs", [])}
    datasets: set[str] = set()
    for spec in case.get("spec_inputs", []):
        if spec.get("type") != spec_type:
            continue
        rows = load_spec_csv(root / spec["path"])
        datasets.update(row["target"].upper() for row in rows if row.get("target"))
    return sorted(datasets & expected)


def _log_event(event: str, details: dict | None = None) -> None:
    st.session_state.session_events.append(
        {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details or {},
        }
    )


st.set_page_config(page_title="AI Synthetic Data Generator", layout="wide")
st.markdown(
    """
<style>
.stApp {
  background:
    radial-gradient(1000px 500px at 0% -10%, rgba(39, 91, 255, 0.25) 0%, transparent 60%),
    radial-gradient(900px 450px at 100% 0%, rgba(20, 184, 166, 0.22) 0%, transparent 55%),
    linear-gradient(160deg, #061426 0%, #0e1f36 58%, #0b1728 100%);
}
h1, h2, h3, label, .stCaption, .stMarkdown, .stText, .stAlert {
  color: #e8f0ff !important;
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f2035 0%, #0b1626 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.25);
}
div[data-testid="stTabs"] button {
  min-width: 160px !important;
  width: 160px !important;
  justify-content: center !important;
  border-radius: 999px !important;
  border: 1px solid rgba(148, 163, 184, 0.25) !important;
  color: #dbeafe !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  background: linear-gradient(90deg, #2563eb, #14b8a6) !important;
  color: #ffffff !important;
  border-color: transparent !important;
}
.stButton > button, .stDownloadButton > button {
  border-radius: 12px !important;
  border: 0 !important;
  color: white !important;
  background: linear-gradient(90deg, #2563eb 0%, #14b8a6 100%) !important;
  font-weight: 700 !important;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.28);
}
.stButton > button:hover, .stDownloadButton > button:hover {
  filter: brightness(1.06);
}
div[data-testid="stFileUploader"] {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 14px;
  padding: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)
st.title("AI Synthetic Data Generator")
st.caption("Generate validated SAS and R code from SDTM or ADaM mapping specs")

if "session_events" not in st.session_state:
    st.session_state.session_events = []
    _log_event("session_started", {})

with st.sidebar:
    st.header("AI Controls")
    routing_mode = st.selectbox("Routing Mode", ["deterministic", "llm", "consensus"], index=0)
    provider = "OpenAI"
    model = "gpt-4o-mini"
    api_key = ""
    parse_temperature = 0.4
    compile_temperature = 0.2
    repair_temperature = 0.1
    repair_retries = 2
    if routing_mode == "deterministic":
        st.caption("Deterministic mode uses the parser and validators only. No API key is needed.")
    else:
        st.caption("LLM modes currently support OpenAI only.")
        st.text_input("Provider", value=provider, disabled=True)
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
        api_key = st.text_input("API Key", type="password")
        st.markdown("---")
        parse_temperature = st.slider("Parse Temperature", 0.0, 1.0, parse_temperature, 0.05)
        compile_temperature = st.slider("Compile Temperature", 0.0, 1.0, compile_temperature, 0.05)
        repair_temperature = st.slider("Repair Temperature", 0.0, 1.0, repair_temperature, 0.05)
        repair_retries = st.slider("Auto-repair Retries", 0, 3, repair_retries, 1)
    st.markdown("---")
    st.header("Session Log")
    st.download_button(
        "Download Session Log (JSON)",
        data=json.dumps(st.session_state.session_events, indent=2),
        file_name="session_log.json",
        mime="application/json",
        use_container_width=True,
    )
    if st.button("Clear Session Log", use_container_width=True):
        st.session_state.session_events = []
        _log_event("session_log_cleared", {})

tab_compile, tab_eval = st.tabs(["Compile", "Eval"])

with tab_compile:
    spec_type = st.radio("Standard", ["SDTM", "ADaM"], horizontal=True, index=0)
    _render_workflow(spec_type)
    cfg = SPEC_CONFIG[spec_type]

    left, right = st.columns([0.9, 1.1])

    with left:
        st.subheader(f"{spec_type} Setup")
        standards_version = st.selectbox(cfg["ig_label"], cfg["versions"], index=0)

        st.subheader(f"{spec_type} Sample")
        st.download_button(
            f"Download sample {spec_type} spec",
            data=_read_bytes(cfg["sample_path"]),
            file_name=cfg["sample_name"],
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("**Spec CSV schema**")
        st.dataframe(
            [
                {"column": "source", "required": "yes", "purpose": "Input dataset name"},
                {"column": "target", "required": "yes", "purpose": f"Output {spec_type} dataset name"},
                {"column": "variable", "required": "yes", "purpose": "Target variable name"},
                {"column": "logic", "required": "yes", "purpose": "Mapping or derivation instruction"},
                {"column": "label", "required": "no", "purpose": "Variable label"},
                {"column": "type", "required": "no", "purpose": "char or num"},
                {"column": "length", "required": "no", "purpose": "Target variable length"},
            ],
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.subheader("Generate Code")
        uploaded = st.file_uploader(f"Upload {spec_type} spec CSV", type=["csv"])
        run = st.button("Generate SAS and R Code", type="primary", use_container_width=True)

    if run:
        if not uploaded:
            st.error("Please upload a spec CSV.")
            _log_event("compile_failed", {"reason": "missing_file"})
        else:
            tmp = ROOT / "data" / "specs" / f"_uploaded_spec_{uuid.uuid4().hex}.csv"
            tmp.write_bytes(uploaded.read())
            _log_event("compile_started", {"spec_type": spec_type, "standards_version": standards_version, "mode": routing_mode})
            try:
                ir, compile_result = run_compile_pipeline(
                    spec_path=str(tmp),
                    spec_type=spec_type,
                    standards_version=standards_version,
                    mode=routing_mode,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    parse_temperature=parse_temperature,
                    compile_temperature=compile_temperature,
                    repair_temperature=repair_temperature,
                    repair_retries=repair_retries,
                )
                sas_code = render_sas(ir)
                r_code = render_r(ir)

                st.subheader("Validation Result")
                st.json(
                    {
                        **compile_result,
                        "runtime_config": {
                            "provider": provider,
                            "model": model,
                            "api_key_set": bool(api_key),
                            "parse_temperature": parse_temperature,
                            "compile_temperature": compile_temperature,
                            "repair_temperature": repair_temperature,
                            "repair_retries": repair_retries,
                            "routing_mode": routing_mode,
                        },
                    }
                )
                st.subheader("IR")
                st.code(json.dumps(asdict(ir), indent=2), language="json")
                _log_event(
                    "compile_completed",
                    {
                        "ok": compile_result.get("ok"),
                        "warnings": len(compile_result.get("warnings", [])),
                        "schema_issues": len(compile_result.get("schema_issues", [])),
                        "semantic_issues": len(compile_result.get("semantic_issues", [])),
                    },
                )

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### SAS Code")
                    st.code(sas_code, language="sas")
                    st.download_button("Download SAS code", sas_code, file_name="generated.sas", mime="text/plain", use_container_width=True)
                with c2:
                    st.markdown("### R Code")
                    st.code(r_code, language="r")
                    st.download_button("Download R code", r_code, file_name="generated.R", mime="text/plain", use_container_width=True)
            except Exception as e:
                _log_event("compile_failed", {"error": str(e)})
                st.error(f"Compile failed: {e}")
            finally:
                if tmp.exists():
                    tmp.unlink()

with tab_eval:
    st.subheader("Golden Case Evaluation")
    st.caption("Eval compares deterministic compiled rows against checked-in expected datasets. It does not run generated SAS or R code.")
    cases_dir = ROOT / "data" / "golden_cases"
    case_files = sorted([p for p in cases_dir.glob("*.json")])
    if not case_files:
        st.warning("No golden case JSON files found in data/golden_cases.")
    else:
        selected_case = st.selectbox(
            "Select Golden Case",
            options=case_files,
            format_func=lambda p: p.name,
        )
        eval_spec_type = st.radio("Standard to Evaluate", ["SDTM", "ADaM"], horizontal=True, index=0)
        dataset_options = _case_dataset_options(selected_case, eval_spec_type)
        if not dataset_options:
            st.warning(f"No {eval_spec_type} datasets were found in this case.")
            selected_dataset = None
            run_eval = False
        else:
            selected_dataset = st.selectbox("Dataset to Evaluate", dataset_options)
            run_eval = st.button("Run Eval Case", type="primary", use_container_width=True)

        if run_eval:
            _log_event(
                "eval_started",
                {
                    "case": selected_case.name,
                    "mode": "data_only",
                    "spec_type": eval_spec_type,
                    "dataset": selected_dataset,
                },
            )
            try:
                result = run_case(
                    selected_case,
                    spec_type_filter=eval_spec_type,
                    dataset_filter=selected_dataset,
                )
                m1, m2, m3 = st.columns(3)
                m1.metric("Checks", result["total_checks"])
                m2.metric("Passed", result["passed_checks"])
                m3.metric("Pass Rate", f"{result['pass_rate']:.1f}%")
                st.caption(f"Status: {result['status']}")
                _log_event(
                    "eval_completed",
                    {
                        "case": selected_case.name,
                        "status": result["status"],
                        "pass_rate": result["pass_rate"],
                        "total_checks": result["total_checks"],
                        "spec_type": eval_spec_type,
                        "dataset": selected_dataset,
                    },
                )

                st.markdown("### Dataset Results")
                for check in result["checks"]:
                    icon = "PASS" if check["ok"] else "FAIL"
                    with st.expander(f"{icon} | {check['spec_type']} | {check['dataset']}"):
                        st.write(f"Rows actual: {check['row_count_actual']}, expected: {check['row_count_expected']}")
                        st.write(f"Row count match: {check['row_count_match']}")
                        st.write(f"Column order/content match: {check['column_match']}")
                        st.write(f"Compared cells: {check['compared_cell_count']}")
                        st.write(f"Matched cells: {check['matched_cell_count']}")
                        st.write(f"Cell mismatches: {check['cell_mismatch_count']}")
                        st.write(f"Rows with any mismatch: {check['row_mismatch_count']}")
                        st.write(f"Issue count: {check['issue_count']}")
                        if check["mismatch_examples"]:
                            st.markdown("Mismatch examples:")
                            st.dataframe(check["mismatch_examples"], use_container_width=True, hide_index=True)
                        if check["issues"]:
                            st.markdown("Issues:")
                            for issue in check["issues"]:
                                st.write(f"- {issue}")
            except Exception as e:
                _log_event(
                    "eval_failed",
                    {
                        "case": selected_case.name,
                        "mode": "data_only",
                        "spec_type": eval_spec_type,
                        "dataset": selected_dataset,
                        "error": str(e),
                    },
                )
                st.error(f"Eval failed: {e}")
