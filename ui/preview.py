import streamlit as st
from core.model_builder import DataModelBuilder
import time


def render_preview_stage():
    """
    STAGE 2.5 — CLEANED DATA PREVIEW & CONFIRMATION
    """

    
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)

    st.markdown("""
    <script>
    const scrollToTop = () => {
        const topElement = window.parent.document.getElementById("top");
        if (topElement) {
            topElement.scrollIntoView({behavior: "instant", block: "start"});
        }
    };
    setTimeout(scrollToTop, 0);
    </script>
    """, unsafe_allow_html=True)


    st.markdown("""
    <style>

    .title-main {
        font-size: 58px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .purple-text {
        color: #a855f7;
        font-weight: 700;
    }

    </style>
    """, unsafe_allow_html=True)

  
    # TITLE

    st.markdown("""
    <div class="title-main" style="margin-top:-55px;">
        Cleaned Data <span class="purple-text">Preview</span>
    </div>
    """, unsafe_allow_html=True)


    # Load session data

    df_clean = st.session_state.cleaned_df
    summary = st.session_state.cleaning_summary
    temp_cfg = st.session_state.temp_model_config


    # PART 1 — CLEANING SUMMARY

    st.subheader("🧹 Cleaning Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Rows Before", summary["rows_before"])

    # Styled metric
    with c2:
        st.markdown(f"""
        <div>
            <div style="font-size:14px; color:#9ca3af;">Rows After</div>
            <div style="
                color:#a855f7;
                font-size:36px;
                font-weight:700;
                line-height:1.2;
            ">
                {summary['rows_after']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    c3.metric("Columns Before", summary["cols_before"])

    with c4:
        st.markdown(f"""
        <div>
            <div style="font-size:14px; color:#9ca3af;">Columns After</div>
            <div style="
                color:#a855f7;
                font-size:36px;
                font-weight:700;
                line-height:1.2;
            ">
                {summary['cols_after']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("**Dropped Columns:**")
    st.write(summary["dropped_columns"] or "None")

    st.markdown("**Row Operations Applied:**")
    st.write(summary["row_operations"] or "None")


    # PART 2 — DATA PREVIEW 

    st.markdown("""
    <h3>📄 Data <span class="purple-text">Preview</span> (First 50 Rows)</h3>
    """, unsafe_allow_html=True)

    # 🔥 Prevent auto-focus issue
    placeholder = st.empty()

    # Small delay ensures scroll happens first
    time.sleep(0.05)

    placeholder.dataframe(df_clean.head(50), use_container_width=True)


    # PART 3 — VALIDATION

    if df_clean.empty:
        st.error("❌ Cleaned data is empty. Please go back and adjust cleaning rules.")
        st.stop()

    if df_clean.shape[0] < 10:
        st.warning(
            "⚠️ Very few rows remain after cleaning. "
            "Analytics and forecasting accuracy may be limited."
        )


    # PART 4 — ACTIONS

    st.markdown("---")

    col_back, col_next = st.columns(2)

    with col_back:
        if st.button("⬅️ Go Back & Edit Cleaning"):
            st.session_state.app_stage = "model"
            st.rerun()

    with col_next:
        if st.button("✅ Confirm & Generate Dashboard"):
            build_data_model(df_clean, temp_cfg)



# HELPER

def build_data_model(df_clean, cfg):

    builder = DataModelBuilder()

    data_model = builder.build(
        df=df_clean,
        dataset_name="User Upload",
        column_profile=cfg["column_profile"],
        measures={
            m: {"column": m, "type": "flow"}
            for m in cfg["measures"]
        },
        dimensions=cfg["dimensions"],
        date_fields=cfg["date_fields"],
        ignored_columns=cfg["ignored_columns"],
    )

    st.session_state.df = df_clean
    st.session_state.data_model = data_model
    st.session_state.app_stage = "report"
    st.rerun()