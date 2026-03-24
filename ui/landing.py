import streamlit as st

def load_css():
    st.markdown("""
    <style>

    /* ---------- CONTAINER WIDTH ---------- */
    .main-container {
        max-width: 900px;
        margin: auto;
    }

    /* ---------- TITLE ---------- */
    .title-main {
        text-align: center;
        font-size: 80px;
        font-weight: 800;
    }

    .title-purple {
        color: #a855f7;
    }

    /* ---------- TYPING ---------- */
    .typing-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 0;
    }

    .typing {
        font-size: 36px;
        color: #cbd5e1;

        margin: 0;
        padding: 0;
        line-height: 1.2;

        white-space: nowrap;
        overflow: hidden;

        border-right: 3px solid #a855f7;

        display: inline-block;

        width: 0;

        animation: typing 6s steps(34, end) forwards, blink 1s infinite;
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 34ch; }
    }

    @keyframes blink {
        50% { border-color: transparent }
    }

    /* ---------- FLOW TEXT ---------- */
    .flow-text {
        text-align: center;
        font-size: 24px;
        margin-top: 10px;
        font-weight: 500;
        background: linear-gradient(90deg, #a855f7, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ---------- CARD ---------- */
    .card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        padding: 25px 15px;
        border-radius: 16px;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #334155;
        cursor: pointer;
        height: 140px;
    }

    .card:hover {
        transform: translateY(-6px);
        border: 1px solid #a855f7;
        box-shadow: 0px 12px 30px rgba(168, 85, 247, 0.4);
    }

    .card-title {
        font-size: 22px;
        font-weight: 600;
        margin-top: 8px;
    }

    /* ---------- BUTTON ---------- */
    .stButton>button {
        width: 240px;
        height: 55px;
        border-radius: 14px;
        font-size: 18px;
        font-weight: 600;

        background: rgba(168, 85, 247, 0.15);
        border: 1px solid rgba(168, 85, 247, 0.4);

        backdrop-filter: blur(10px);

        box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);

        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: rgba(168, 85, 247, 0.3);
        box-shadow: 0 0 35px rgba(168, 85, 247, 0.9);
        transform: scale(1.05);
    }

    </style>
    """, unsafe_allow_html=True)


# ================================
# LANDING PAGE
# ================================
def render_landing():

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # ---------- TITLE ----------
    st.markdown("""
    <div class="title-main">
        <span class="title-purple">Smart</span>Dash<span class="title-purple">AI</span>
    </div>
    """, unsafe_allow_html=True)

    # ---------- SUBTITLE ----------
    st.markdown("""
    <div class="typing-container">
        <div class="typing">
            AI-Powered Data Analytics Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- FLOW TEXT ----------
    st.markdown("""
    <div class="flow-text">
        Upload Data → Analyze → Forecast → Decide
    </div>
    """, unsafe_allow_html=True)

    # ---------- CARDS ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">📊 Auto Dashboard</div>
            <div>Generate insights instantly</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">🧠 Data Health AI</div>
            <div>Evaluate data quality</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">📈 Smart Forecasting</div>
            <div>Predict future trends</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ---------- BUTTON ----------
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("🚀 Get Started"):
            st.session_state.app_stage = "import"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)