from pathlib import Path
import sys
import json
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


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


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
st.caption("Version-aware spec validation + dual SAS/R code generation")

if "session_events" not in st.session_state:
    st.session_state.session_events = []
    _log_event("session_started", {})

with st.sidebar:
    st.header("AI Controls")
    provider = st.selectbox("Provider", ["OpenAI", "Google Gemini", "Anthropic Claude"], index=0)
    provider_models = {
        "OpenAI": ["gpt-4o-mini", "gpt-4o"],
        "Google Gemini": ["gemini-2.0-flash", "gemini-1.5-pro"],
        "Anthropic Claude": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
    }
    model = st.selectbox("Model", provider_models[provider], index=0)
    api_key = st.text_input("API Key", type="password")
    st.markdown("---")
    parse_temperature = st.slider("Parse Temperature", 0.0, 1.0, 0.4, 0.05)
    compile_temperature = st.slider("Compile Temperature", 0.0, 1.0, 0.2, 0.05)
    repair_temperature = st.slider("Repair Temperature", 0.0, 1.0, 0.1, 0.05)
    repair_retries = st.slider("Auto-repair Retries", 0, 3, 2, 1)
    routing_mode = st.selectbox("Routing Mode", ["deterministic", "llm", "consensus"], index=0)
    st.markdown("---")
    st.caption("LLM/repair controls are active for `llm` and `consensus` modes.")
    st.header("Execution Runtimes")
    sas_executable = st.text_input("SAS executable path (optional)", value="")
    rscript_executable = st.text_input("Rscript path (optional)", value="")
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
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Configuration")
        spec_type = st.selectbox("Spec Type", ["SDTM", "ADaM"], index=0)
        sdtm_ver = st.selectbox("SDTMIG Version", ["3.3", "3.4"], index=0)
        adam_ver = st.selectbox("ADaMIG Version", ["1.2", "1.3"], index=0)
        standards_version = sdtm_ver if spec_type == "SDTM" else adam_ver

        st.subheader("Sample Specs")
        st.download_button(
            "Download sample SDTM spec",
            data=_read_bytes(ROOT / "data" / "specs" / "sample_sdtm_spec.csv"),
            file_name="sample_sdtm_spec.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download sample ADaM spec",
            data=_read_bytes(ROOT / "data" / "specs" / "sample_adam_spec.csv"),
            file_name="sample_adam_spec.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with right:
        st.subheader("Upload and Compile")
        uploaded = st.file_uploader("Upload spec CSV", type=["csv"])
        run = st.button("Generate Code", type="primary", use_container_width=True)

    if run:
        if not uploaded:
            st.error("Please upload a spec CSV.")
            _log_event("compile_failed", {"reason": "missing_file"})
        else:
            tmp = ROOT / "data" / "specs" / "_uploaded_spec.csv"
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
        eval_mode = st.radio("Eval Mode", ["data_only", "execute_generated_code"], horizontal=True)
        run_eval = st.button("Run Eval Case", type="primary", use_container_width=True)

        if run_eval:
            _log_event("eval_started", {"case": selected_case.name, "mode": eval_mode})
            try:
                result = run_case(
                    selected_case,
                    execute_generated_code=(eval_mode == "execute_generated_code"),
                    sas_executable=(sas_executable.strip() or None),
                    rscript_executable=(rscript_executable.strip() or None),
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
                    },
                )

                st.markdown("### Dataset Results")
                for check in result["checks"]:
                    icon = "PASS" if check["ok"] else "FAIL"
                    with st.expander(f"{icon} | {check['spec_type']} | {check['dataset']}"):
                        st.write(f"Rows actual: {check['row_count_actual']}, expected: {check['row_count_expected']}")
                        st.write(f"Issue count: {check['issue_count']}")
                        if check["issues"]:
                            st.markdown("Issues:")
                            for issue in check["issues"]:
                                st.write(f"- {issue}")
                if result.get("execution_reports"):
                    st.markdown("### Code Execution Reports")
                    for rep in result["execution_reports"]:
                        with st.expander(f"{rep.get('engine')} | {rep.get('status')}"):
                            st.json(rep)
            except Exception as e:
                _log_event("eval_failed", {"case": selected_case.name, "mode": eval_mode, "error": str(e)})
                st.error(f"Eval failed: {e}")
