import streamlit as st
from core.model_builder import DataModelBuilder


def render_preview_stage():
    """
    STAGE 2.5 — CLEANED DATA PREVIEW & CONFIRMATION

    Responsibilities:
    - Show summary of cleaning operations
    - Preview cleaned dataset
    - Validate data sufficiency
    - Confirm and build final Data Model
    """

    st.title("Cleaned Data Preview")

    # ---------------------------------------------
    # Load session data
    # ---------------------------------------------
    df_clean = st.session_state.cleaned_df
    summary = st.session_state.cleaning_summary
    temp_cfg = st.session_state.temp_model_config

    # =================================================
    # PART 1 — CLEANING SUMMARY
    # =================================================
    st.subheader("🧹 Cleaning Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows Before", summary["rows_before"])
    c2.metric("Rows After", summary["rows_after"])
    c3.metric("Columns Before", summary["cols_before"])
    c4.metric("Columns After", summary["cols_after"])

    st.markdown("**Dropped Columns:**")
    st.write(summary["dropped_columns"] or "None")

    st.markdown("**Row Operations Applied:**")
    st.write(summary["row_operations"] or "None")

    # =================================================
    # PART 2 — DATA PREVIEW
    # =================================================
    st.subheader("📄 Data Preview (First 50 Rows)")
    st.dataframe(df_clean.head(50), use_container_width=True)

    # =================================================
    # PART 3 — VALIDATION WARNINGS
    # =================================================
    if df_clean.empty:
        st.error("❌ Cleaned data is empty. Please go back and adjust cleaning rules.")
        st.stop()

    if df_clean.shape[0] < 10:
        st.warning(
            "⚠️ Very few rows remain after cleaning. "
            "Analytics and forecasting accuracy may be limited."
        )

    # =================================================
    # PART 4 — USER ACTIONS
    # =================================================
    st.markdown("---")
    col_back, col_next = st.columns(2)

    with col_back:
        if st.button("⬅️ Go Back & Edit Cleaning"):
            st.session_state.app_stage = "model"
            st.rerun()

    with col_next:
        if st.button("✅ Confirm & Generate Dashboard"):
            build_data_model(df_clean, temp_cfg)


# -------------------------------------------------
# Helper: Build final data model
# -------------------------------------------------
def build_data_model(df_clean, cfg):
    """
    Builds the final DataModel object used by the report,
    analytics engine, forecasting, and chat assistant.
    """

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

    # Persist for downstream stages
    st.session_state.df = df_clean
    st.session_state.data_model = data_model
    st.session_state.app_stage = "report"
    st.rerun()
