import streamlit as st

from ui.landing import render_landing
from ui.import_stage import render_import_stage
from ui.modeling import render_modeling_stage
from ui.preview import render_preview_stage
from ui.report import render_report_stage



st.set_page_config(
    page_title="SmartDashAI",
    layout="wide",
    initial_sidebar_state="expanded"
)




if "app_stage" not in st.session_state:
    st.session_state.app_stage = "landing"

# ROUTER

stage = st.session_state.app_stage

if stage == "landing":
    render_landing()

elif stage == "import":
    render_import_stage()

elif stage == "model":
    render_modeling_stage()

elif stage == "preview":
    render_preview_stage()

elif stage == "report":
    render_report_stage()