import streamlit as st



# LOAD CSS

def load_css():
    st.markdown("""
    <style>

    .main-container {
        max-width: 900px;
        margin: auto;
    }

    .title-main {
        text-align: center;
        font-size: 80px;
        font-weight: 800;
    }

    .title-purple {
        color: #a855f7;
    }

    .typing-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
    }

    .typing {
        font-size: 36px;
        color: #cbd5e1;
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

    .flow-text {
        text-align: center;
        color: #a855f7;
        font-size: 24px;
        margin-top: 10px;
        margin-bottom: 60px;
        font-weight: 500;
    }

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
        font-size: 32px;
        font-weight: 600;
        margin-top: 8px;
    }

    /* BUTTON STYLE */
    .stButton > button {
        width: 100%;
        height: 60px;
        border-radius: 14px;
        font-size: 30px;
        font-weight: 700;

        background: rgba(168, 85, 247, 0.15);
        border: 1px solid rgba(168, 85, 247, 0.4);

        backdrop-filter: blur(10px);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);

        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: rgba(168, 85, 247, 0.3);
        box-shadow: 0 0 35px rgba(168, 85, 247, 0.9);
        transform: scale(1.05);
    }

    </style>
    """, unsafe_allow_html=True)



# LANDING PAGE

def render_landing():

    load_css()

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    #  TITLE 
    st.markdown("""
    <div class="title-main">
        <span class="title-purple">Smart</span>Dash<span class="title-purple">AI</span>
    </div>
    """, unsafe_allow_html=True)

    # SUBTITLE 
    st.markdown("""
    <div class="typing-container">
        <div class="typing">
            AI-Powered Data Analytics Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    #FLOW 
    st.markdown("""
    <div class="flow-text">
        Upload Data → Analyze → Forecast → Decide
    </div>
    """, unsafe_allow_html=True)

    # CARDS
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">Auto Dashboard</div>
            <div>Generate insights instantly</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">Data Health AI</div>
            <div>Evaluate data quality</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">Smart Forecasting</div>
            <div>Predict future trends</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 2, 3])

    with col2:
        if st.button("Get Started", use_container_width=True, key="get_started_btn"):
            st.session_state.app_stage = "import"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


