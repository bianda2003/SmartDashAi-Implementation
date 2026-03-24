import streamlit as st
import pandas as pd

from core.profiler import DataProfiler


def render_modeling_stage():
    """
    STAGE 2 — DATA INTELLIGENCE & CLEANSING

    Responsibilities:
    - Recommend bad columns (profiling-based)
    - Allow user-driven column & row cleansing
    - Define analytics logic (Measures, Dimensions, Dates)
    - Persist cleaned dataset & modeling configuration

    NOTE:
    - No data is modified permanently until user confirms
    - All outputs are stored in st.session_state for downstream stages
    """

    st.title("Data Intelligence & Cleansing")

    # ---------------------------------------------
    # Load required session data
    # ---------------------------------------------
    df = st.session_state.df
    profile_df = st.session_state.profile_df
    profiler = DataProfiler()

    # ---------------------------------------------
    # Session defaults (safe initialization)
    # ---------------------------------------------
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = None

    if "cleaning_summary" not in st.session_state:
        st.session_state.cleaning_summary = {}

    # =================================================
    # PART 1 — COLUMN CLEANSING
    # =================================================
    st.subheader("1️ Column Cleansing (Remove Bad Features)")

    drop_recommendations = profiler.recommend_drops(df, profile_df)

    if drop_recommendations:
        st.info("💡 Recommended Columns to Drop")
        rec_df = pd.DataFrame(
            list(drop_recommendations.items()),
            columns=["Column", "Reason"]
        )
        st.table(rec_df)
        default_drops = list(drop_recommendations.keys())
    else:
        st.success("✅ No problematic columns detected.")
        default_drops = []

    cols_to_drop = st.multiselect(
        "Select columns to drop",
        options=df.columns.tolist(),
        default=default_drops
    )

    # =================================================
    # PART 2 — ROW CLEANSING
    # =================================================
    st.subheader("2️ Row Cleansing (Remove Bad Records)")

    row_issues = profiler.detect_row_issues(df)
    row_operations = []

    if not row_issues:
        st.success("✅ No duplicate or null rows detected.")
    else:
        c1, c2 = st.columns(2)

        if "duplicates" in row_issues:
            with c1:
                st.warning(f"⚠️ {row_issues['duplicates']} duplicate rows found.")
                if st.checkbox("Remove duplicate rows"):
                    row_operations.append("duplicates")

        if "rows_with_nulls" in row_issues:
            with c2:
                st.warning(f"⚠️ {row_issues['rows_with_nulls']} rows with missing values.")
                if st.checkbox("Remove rows with missing values"):
                    row_operations.append("missing")

    # =================================================
    # PART 3 — ANALYTICS LOGIC DEFINITION
    # =================================================
    st.markdown("---")
    st.subheader("3️ Define Analytics Logic")

    # Columns that survive column cleansing
    remaining_cols = [c for c in df.columns if c not in cols_to_drop]

    # ---- Identify numeric & date columns
    numeric_cols = profile_df[
        (profile_df["Detected Type"] == "numeric") &
        (profile_df["Column"].isin(remaining_cols))
    ]["Column"].tolist()

    date_cols = profile_df[
        (profile_df["Detected Type"] == "datetime") &
        (profile_df["Column"].isin(remaining_cols))
    ]["Column"].tolist()

    # ---- Ignore spec-like / non-business metrics
    ignore_keywords = [
        "id", "index", "code", "isbn",
        "ram", "rom", "storage", "battery",
        "inch", "cm", "mm", "pixel",
        "weight", "gram", "kg", "hz", "core"
    ]

    suggested_measures = [
        col for col in numeric_cols
        if not any(k in col.lower() for k in ignore_keywords)
        and df[col].nunique() > 5
    ]

    dimension_candidates = [
        col for col in remaining_cols
        if col not in suggested_measures
    ]

    c1, c2 = st.columns(2)

    with c1:
        measures = st.multiselect(
            "Measures (Business Metrics)",
            options=numeric_cols,
            default=suggested_measures,
            help="Examples: Sales, Profit, Quantity"
        )

    with c2:
        dimensions = st.multiselect(
            "Dimensions (Categories)",
            options=remaining_cols,
            default=dimension_candidates[:5]
        )

    date_fields = st.multiselect(
        "Date Fields (For Forecasting)",
        options=remaining_cols,
        default=date_cols
    )

    # =================================================
    # PART 4 — PREVIEW & SAVE MODEL CONFIG
    # =================================================
    st.markdown("---")

    if st.button("🔍 Preview Cleaned Data"):
        if not measures or not dimensions:
            st.error("❌ Please select at least one Measure and one Dimension.")
            return

        # ---- Apply column cleansing
        final_df = df.drop(columns=cols_to_drop)

        # ---- Apply row cleansing
        if "duplicates" in row_operations:
            final_df = final_df.drop_duplicates()

        if "missing" in row_operations:
            final_df = final_df.dropna()

        # ---- Persist results
        st.session_state.cleaned_df = final_df

        st.session_state.cleaning_summary = {
            "rows_before": df.shape[0],
            "rows_after": final_df.shape[0],
            "cols_before": df.shape[1],
            "cols_after": final_df.shape[1],
            "dropped_columns": cols_to_drop,
            "row_operations": row_operations,
        }

        st.session_state.temp_model_config = {
            "measures": measures,
            "dimensions": dimensions,
            "date_fields": date_fields,
            "ignored_columns": cols_to_drop,
            "column_profile": profile_df[
                profile_df["Column"].isin(remaining_cols)
            ]
        }

        # ---- Move to preview stage
        st.session_state.app_stage = "preview"
        st.rerun()
