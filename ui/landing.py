import streamlit as st

def render_landing():
    st.markdown("""
    <div style='text-align:center; padding:40px'>
        <h1>SmartDashAI</h1>
        <h3>AI-Powered Data Analytics Platform</h3>
        <p>Upload data → Analyze → Forecast → Decide</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    col1.info("Auto Dashboard")
    col2.info("Data Health AI")
    col3.info("Smart Forecasting")

    st.markdown("")

    if st.button("Get Started", use_container_width=True):
        st.session_state.app_stage = "import"
        st.rerun()