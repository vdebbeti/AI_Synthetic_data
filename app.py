from pathlib import Path
import sys
import json

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sdtm_adam_compiler.orchestration.spec_to_ir import build_ir_from_spec
from sdtm_adam_compiler.orchestration.compiler import compile_ir
from sdtm_adam_compiler.renderers.sas_renderer import render_sas
from sdtm_adam_compiler.renderers.r_renderer import render_r


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


st.set_page_config(page_title="SDTM/ADaM Spec Compiler", layout="wide")
st.title("SDTM/ADaM Spec Compiler")
st.caption("Version-aware spec validation + dual SAS/R code generation")

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
    else:
        tmp = ROOT / "data" / "specs" / "_uploaded_spec.csv"
        tmp.write_bytes(uploaded.read())
        try:
            ir = build_ir_from_spec(str(tmp), spec_type)
            compile_result = compile_ir(ir, standards_version=standards_version)
            sas_code = render_sas(ir)
            r_code = render_r(ir)

            st.subheader("Validation Result")
            st.json(compile_result)
            st.subheader("IR")
            st.code(json.dumps(ir, default=lambda o: o.__dict__, indent=2), language="json")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### SAS Code")
                st.code(sas_code, language="sas")
                st.download_button("Download SAS code", sas_code, file_name="generated.sas", mime="text/plain", use_container_width=True)
            with c2:
                st.markdown("### R Code")
                st.code(r_code, language="r")
                st.download_button("Download R code", r_code, file_name="generated.R", mime="text/plain", use_container_width=True)
        finally:
            if tmp.exists():
                tmp.unlink()

