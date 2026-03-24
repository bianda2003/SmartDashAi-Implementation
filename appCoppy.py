import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


from core.data_loader import DataLoader
from core.profiler import DataProfiler
from core.model_builder import DataModelBuilder
from core.analytics_engine import AnalyticsEngine
from core.forecast_engine import ForecastEngine
from core.chat_engine import ChatEngine
from core.forecast_engine import ForecastEngine, smape

# =================================================
# STAGE 0 — LANDING PAGE
# =================================================
if "app_stage" not in st.session_state:
    st.session_state.app_stage = "landing"

if st.session_state.app_stage == "landing":
    st.markdown(
        """
        <h1 style='text-align:center; font-size:64px;'>🚀 SmartDashAI</h1>
        <h3 style='text-align:center; font-weight:300;'>
        Intelligent Data Analytics & Forecasting Platform
        </h3>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        """
        ### What SmartDashAI does
        - 📊 Automatically builds dashboards from raw data  
        - 🧠 Applies intelligent data modeling & cleansing  
        - 🩺 Evaluates **Data Health** before forecasting  
        - 🔮 Generates explainable AI forecasts  

        Designed to help **non-technical users** make **data-driven decisions**.
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Let’s Get Started", use_container_width=True):
            st.session_state.app_stage = "import"
            st.rerun()
def compute_performance_score(df, dimension_col, measure_cols, weights=None):
    """
    Generic Product/Item Performance Score
    Works with any dataset that has:
    - One dimension (e.g., Product)
    - Numeric measures (e.g., Sales, Profit, Quantity)
    """

    if weights is None:
        weights = {}

    # Aggregate metrics by dimension
    agg_df = df.groupby(dimension_col)[measure_cols].sum().reset_index()

    score = pd.Series(0, index=agg_df.index, dtype=float)

    for col in measure_cols:
        if agg_df[col].max() == 0:
            continue

        normalized = agg_df[col] / agg_df[col].max()
        weight = weights.get(col, 1 / len(measure_cols))
        score += normalized * weight

    agg_df["Performance_Score"] = score.round(3)

    return agg_df.sort_values("Performance_Score", ascending=False)



# =================================================
# Time Intelligence Helpers (Reusable)
# =================================================
def render_ytd_mtd_kpis(filtered_df, data_model):
    """
    Renders YTD and MTD KPI cards safely.
    """
    if (
        data_model is None
        or not data_model.date_fields
        or "Sales" not in data_model.measures
        or filtered_df.empty
    ):
        return

    date_col = data_model.date_fields[0]
    sales_col = data_model.measures["Sales"]["column"]

    analytics = AnalyticsEngine(filtered_df, data_model)

    try:
        ytd_value = analytics.compute_ytd(filtered_df, date_col, sales_col)
        mtd_value = analytics.compute_mtd(filtered_df, date_col, sales_col)

        c1, c2 = st.columns(2)
        c1.metric("📆 YTD Sales", f"{ytd_value:,.2f}")
        c2.metric("🗓️ MTD Sales", f"{mtd_value:,.2f}")

    except Exception as e:
        st.warning(f"YTD / MTD calculation skipped: {e}")

        


# =================================================
# App Config
# =================================================
st.set_page_config(page_title="SmartDashAI", layout="wide")

# =================================================
# Session State Management
# =================================================
if "app_stage" not in st.session_state:
    st.session_state.app_stage = "import"

if "df" not in st.session_state:
    st.session_state.df = None

if "profile_df" not in st.session_state:
    st.session_state.profile_df = None

if "data_model" not in st.session_state:
    st.session_state.data_model = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chat_input_widget" not in st.session_state:
    st.session_state.chat_input_widget = ""

# =================================================
# STAGE 1 — DATA IMPORT
# =================================================
if st.session_state.app_stage == "import":
    st.title("📂 Import Data")
    st.markdown("Upload your dataset (CSV) to get started.")
    
    if st.button("🎲 Generate Multi-Year Sample Data"):
        np.random.seed(42)

        dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")

        products = [
            ("Laptop", "Electronics", 1200, 900),
            ("Smartphone", "Electronics", 800, 550),
            ("Tablet", "Electronics", 600, 420),
            ("Headphones", "Accessories", 150, 90),
            ("Smartwatch", "Accessories", 250, 160),
            ("Printer", "Office", 400, 300),
        ]

        regions = ["North", "South", "East", "West"]

        rows = []

        for date in dates:
            daily_transactions = np.random.randint(3, 8)

            for _ in range(daily_transactions):
                product, category, unit_price, unit_cost = products[
                    np.random.randint(len(products))
                ]

                quantity = np.random.randint(1, 10)

                sales_amount = quantity * unit_price
                cost_amount = quantity * unit_cost
                profit = sales_amount - cost_amount

                rows.append({
                    "Date": date,
                    "Product": product,
                    "Category": category,
                    "Region": np.random.choice(regions),
                    "Quantity": quantity,
                    "Unit_Price": unit_price,
                    "Unit_Cost": unit_cost,
                    "Sales_Amount": sales_amount,
                    "Cost_Amount": cost_amount,
                    "Profit": profit,
                })

        df = pd.DataFrame(rows)

        # ✅ EVERYTHING that uses df stays INSIDE
        profiler = DataProfiler()
        st.session_state.df = df
        st.session_state.profile_df = profiler.profile(df)
        st.session_state.app_stage = "model"
        st.rerun()



    # --- File Uploader ---
    uploaded_file = st.file_uploader("Or choose a CSV file", type="csv")

    if uploaded_file:
        try:
            loader = DataLoader()
            df = loader.load(uploaded_file)
            
            # Initial Profiling
            profiler = DataProfiler()
            profile_df = profiler.profile(df)

            st.session_state.df = df
            st.session_state.profile_df = profile_df
            st.session_state.app_stage = "model"
            st.rerun()

        except Exception as e:
            st.error(f"Error loading file: {e}")
            

# =================================================
# STAGE 2 — INTELLIGENT DATA MODELING & CLEANSING
# =================================================
elif st.session_state.app_stage == "model":
    st.title(" Data Intelligence & Cleansing")
    
    
    df = st.session_state.df
    profile_df = st.session_state.profile_df
    profiler = DataProfiler()

    # ------------------------------------------------
    # PART A: COLUMN CLEANSING
    # ------------------------------------------------

    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = None

    if "cleaning_summary" not in st.session_state:
        st.session_state.cleaning_summary = {}

    st.subheader("1. Column Cleansing (Remove Bad Features)")
    
    drop_recs = profiler.recommend_drops(df, profile_df)
    
    if drop_recs:
        st.info("💡 Suggestions:")
        rec_table = pd.DataFrame(list(drop_recs.items()), columns=["Column Name", "Reason"])
        st.table(rec_table)
        default_drops = list(drop_recs.keys())
    else:
        st.success("✅ Columns look good.")
        default_drops = []

    cols_to_drop = st.multiselect("Select columns to drop:", df.columns, default=default_drops)

    # ------------------------------------------------
    # PART B: ROW CLEANSING
    # ------------------------------------------------
    st.subheader("2. Row Cleansing (Remove Bad Records)")
    
    row_issues = profiler.detect_row_issues(df)
    clean_ops = [] 
    
    if not row_issues:
        st.success("✅ No duplicate or empty rows found.")
    else:
        col1, col2 = st.columns(2)
        if "duplicates" in row_issues:
            with col1:
                st.warning(f"⚠️ Found {row_issues['duplicates']} duplicate rows.")
                if st.checkbox("Remove Duplicates"):
                    clean_ops.append("duplicates")
        if "rows_with_nulls" in row_issues:
            with col2:
                st.warning(f"⚠️ Found {row_issues['rows_with_nulls']} rows with missing values.")
                if st.checkbox("Remove Rows with Missing Values"):
                    clean_ops.append("missing")

                    


    # ------------------------------------------------
    # PART C: ANALYTICS LOGIC
    # ------------------------------------------------
    st.markdown("---")
    st.subheader("3. Define Analytics Logic")
    
    remaining_cols = [c for c in df.columns if c not in cols_to_drop]
    
    numeric_cols = profile_df[
        (profile_df["Detected Type"] == "numeric") & 
        (profile_df["Column"].isin(remaining_cols))
    ]["Column"].tolist()

    date_cols = profile_df[
        (profile_df["Detected Type"] == "datetime") & 
        (profile_df["Column"].isin(remaining_cols))
    ]["Column"].tolist()

    # --- Filter for "Useless Metrics" ---
    ignore_keywords = [
        "year", "month", "id", "index", "code", "isbn", 
        "inch", "cm", "mm", "pixel", "resolution", 
        "ram", "rom", "storage", "battery", "mah", "wh", 
        "weight", "gram", "kg", "lb", "hz", "core"
    ]

    suggested_measures = [
        c for c in numeric_cols 
        if not any(k in c.lower() for k in ignore_keywords) 
        and df[c].nunique() > 5 
    ]
    
    dimension_candidates = [c for c in remaining_cols if c not in suggested_measures]

    c1, c2 = st.columns(2)
    with c1:
        measures = st.multiselect(
            "Measures (Business Metrics)", 
            numeric_cols, 
            default=suggested_measures,
            help="Select columns like Sales, Profit, Quantity."
        )
    with c2:
        dimensions = st.multiselect(
            "Dimensions (Categories)", 
            remaining_cols, 
            default=dimension_candidates[:5]
        )
    
    date_fields = st.multiselect("Date Fields (For Forecasting)", remaining_cols, default=date_cols)

    # ------------------------------------------------
    # FINAL PROCESSING
    # ------------------------------------------------
    st.markdown("---")
    if st.button("🔍 Preview Cleaned Data"):
        if not measures or not dimensions:
            st.error("Please select at least one Measure and one Dimension.")
        else:
            final_df = df.drop(columns=cols_to_drop)

            if "duplicates" in clean_ops:
                final_df = final_df.drop_duplicates()

            if "missing" in clean_ops:
                final_df = final_df.dropna()

            # Store cleaned data
            st.session_state.cleaned_df = final_df

            # Store cleaning summary
            st.session_state.cleaning_summary = {
                "rows_before": df.shape[0],
                "rows_after": final_df.shape[0],
                "cols_before": df.shape[1],
                "cols_after": final_df.shape[1],
                "dropped_columns": cols_to_drop,
                "row_operations": clean_ops,
            }

            # Store model config (TEMP)
            st.session_state.temp_model_config = {
                "measures": measures,
                "dimensions": dimensions,
                "date_fields": date_fields,
                "ignored_columns": cols_to_drop,
                "column_profile": profile_df[profile_df["Column"].isin(remaining_cols)]
            }

            st.session_state.app_stage = "preview"
            st.rerun()

                # =================================================
# STAGE 2.5 — CLEANED DATA PREVIEW & CONFIRMATION
# =================================================
elif st.session_state.app_stage == "preview":
    st.title("🔍 Cleaned Data Preview")

    df_clean = st.session_state.cleaned_df
    summary = st.session_state.cleaning_summary

    # -----------------------------
    # Cleaning Summary
    # -----------------------------
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

    # -----------------------------
    # Data Preview
    # -----------------------------
    st.subheader("📄 Preview (First 50 Rows)")
    st.dataframe(df_clean.head(50), use_container_width=True)

    # -----------------------------
    # Data Validation Warnings
    # -----------------------------
    if df_clean.empty:
        st.error("❌ Cleaned data is empty. Go back and adjust cleaning rules.")
        st.stop()

    if df_clean.shape[0] < 10:
        st.warning("⚠️ Very few rows remain after cleaning. Dashboard insights may be weak.")

    # -----------------------------
    # Actions
    # -----------------------------
    st.markdown("---")
    col_back, col_next = st.columns([1, 1])

    with col_back:
        if st.button("⬅️ Go Back & Edit Cleaning"):
            st.session_state.app_stage = "model"
            st.rerun()

    with col_next:
        if st.button("✅ Confirm & Generate Dashboard"):
            cfg = st.session_state.temp_model_config

            builder = DataModelBuilder()
            data_model = builder.build(
                df=df_clean,
                dataset_name="User Upload",
                column_profile=cfg["column_profile"],
                measures={m: {"column": m, "type": "flow"} for m in cfg["measures"]},
                dimensions=cfg["dimensions"],
                date_fields=cfg["date_fields"],
                ignored_columns=cfg["ignored_columns"],
            )

            st.session_state.df = df_clean
            st.session_state.data_model = data_model
            st.session_state.app_stage = "report"
            st.rerun()



# =================================================
# STAGE 3 — REPORT VIEW
# =================================================
elif st.session_state.app_stage == "report":
    data_model = st.session_state.data_model
    df = st.session_state.df
    engine = AnalyticsEngine(df, data_model)
    active_filters = {}
    filtered_df = engine.apply_filters(active_filters)


    st.title("📊 SmartDashAI Report")

    # =============================================
    # SIDEBAR: CONTROL PANEL
    # =============================================
    st.sidebar.title("🛠️ Report Settings")
    
    # --- 1. KPI SELECTION (Top) ---
    st.sidebar.subheader("1. KPI Cards")
    
    # Get all possible measures
    valid_kpis = list(data_model.measures.keys())
    
    # Smart default: Hide spec-like columns (ram, weight, etc)
    default_selection = [k for k in valid_kpis if not any(x in k.lower() for x in ['ram', 'inch', 'weight', 'battery'])]
    if not default_selection: default_selection = valid_kpis[:4]
    
    selected_kpis = st.sidebar.multiselect(
        "Display Metrics",
        options=valid_kpis,
        default=default_selection
    )

    st.sidebar.markdown("---")

    

    

    # --- 2. CATEGORY FILTERS (Dropdowns) ---
    st.sidebar.subheader("2. Category Filters")
    active_filters = {}
    
    for dim in data_model.dimensions[:5]: # Limit to top 5 dims
        options = sorted(df[dim].unique().astype(str))
        val = st.sidebar.multiselect(f"{dim}", options=options)
        active_filters[dim] = val

    # Apply Category Filters first
    filtered_df = engine.apply_filters(active_filters)

    st.sidebar.markdown("---")

    # --- 3. LEVEL SELECTIONS (Numeric Ranges) ---
    st.sidebar.subheader("3. Value Ranges")
    
    # Create sliders for the selected Measures
    for measure_name in selected_kpis:
        col_name = data_model.measures[measure_name]["column"]
        
        # Ensure it's numeric before making a slider
        if pd.api.types.is_numeric_dtype(df[col_name]):
            min_val = float(df[col_name].min())
            max_val = float(df[col_name].max())
            
            if min_val < max_val: # Only show slider if there is a range
                rng = st.sidebar.slider(
                    f"{measure_name} Range",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)
                )
                
                # Apply Range Filter directly
                filtered_df = filtered_df[
                    (filtered_df[col_name] >= rng[0]) & 
                    (filtered_df[col_name] <= rng[1])
                ]
    
    if st.sidebar.button("Start Over"):
        st.session_state.clear()
        st.rerun()

    # =============================================
    # MAIN DASHBOARD AREA
    # =============================================

    # --- Display KPIs ---
    current_kpis = engine.compute_kpis(filtered_df)
    
    if selected_kpis:
        kpi_cols = st.columns(len(selected_kpis))
        for i, label in enumerate(selected_kpis):
            with kpi_cols[i]:
                # Show value if it exists in current_kpis, else 0
                val = current_kpis.get(label, 0)
                st.metric(label=label, value=f"{val:,.2f}")
    else:
        st.info("Select metrics from the sidebar to see KPIs.")
     
    st.markdown("---")


    # -------------------------------------------------
# IMPROVED YTD & MTD PERFORMANCE SECTION
# -------------------------------------------------
if (
    st.session_state.get("data_model") is not None
    and st.session_state.get("df") is not None
):
    dm = st.session_state.data_model
    df_local = filtered_df 

    if dm.date_fields and dm.measures and not df_local.empty:
        date_col = dm.date_fields[0]
        # Dynamically pick 'Sales' or the first available measure
        target_measure_name = "Sales" if "Sales" in dm.measures else list(dm.measures.keys())[0]
        measure_col = dm.measures[target_measure_name]["column"]

        try:
            analytics = AnalyticsEngine(df_local, dm)

            ytd_value, mtd_value = analytics.compute_time_kpis(
            df_local,
            date_col,
            target_measure_name
)


            
            # 1. Compute Data
            ytd_value = analytics.compute_ytd(df_local, date_col, measure_col)
            mtd_value = analytics.compute_mtd(df_local, date_col, measure_col)
            comp_df = analytics.compute_ytd_comparison(df_local, date_col, measure_col)

            # 2. Render UI Layout
            st.subheader(f"📈 {target_measure_name} Performance Analysis")
            col_kpi1, col_kpi2, col_chart = st.columns([1, 1, 2])
            
            with col_kpi1:
                st.metric(f"📆 YTD {target_measure_name}", f"{ytd_value:,.2f}")
            with col_kpi2:
                st.metric(f"🗓️ MTD {target_measure_name}", f"{mtd_value:,.2f}")
            
            with col_chart:
                required_cols = {"Month", "Year", "Value"}

                if (
                    comp_df is not None
                    and not comp_df.empty
                    and required_cols.issubset(comp_df.columns)
                    and comp_df["Month"].nunique() >= 2
                ):
                    fig_comp = px.line(
                        comp_df,
                        x="Month",
                        y="Value",
                        color="Year",
                        markers=True,
                        title="YTD vs Previous Year Trend"
                    )
                    fig_comp.update_layout(
                        height=250,
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                else:
                    st.info("Not enough time data for year-over-year comparison.")


        except Exception as e:
            st.warning(f"Performance chart skipped: {e}")

        # =================================================
        # 🏆 PRODUCT PERFORMANCE SCORE (STEP 2)
        # =================================================
        st.markdown("---")
        st.subheader("🏆 Product Performance Score")

        dm = st.session_state.data_model
        df_report = filtered_df

        # Pick dimension safely
        dimension_col = (
            "Product" if "Product" in dm.dimensions
            else dm.dimensions[0]
        )

        # Pick numeric measures
        candidate_measures = []
        for m, meta in dm.measures.items():
            col = meta["column"]
            if pd.api.types.is_numeric_dtype(df_report[col]):
                candidate_measures.append(col)

        priority_keywords = ["sales", "profit", "quantity"]
        ordered_measures = sorted(
            candidate_measures,
            key=lambda x: any(k in x.lower() for k in priority_keywords),
            reverse=True
        )

        selected_measures = ordered_measures[:3]

        if len(selected_measures) < 2:
            st.info("Not enough numeric measures to compute performance score.")
        else:
            weights = {}
            for col in selected_measures:
                if "sales" in col.lower():
                    weights[col] = 0.5
                elif "profit" in col.lower():
                    weights[col] = 0.4
                elif "quantity" in col.lower():
                    weights[col] = 0.1
                else:
                    weights[col] = 1 / len(selected_measures)

            score_df = compute_performance_score(
                df_report,
                dimension_col,
                selected_measures,
                weights
            )

            c1, c2 = st.columns([2, 1])

            with c1:
                fig = px.bar(
                    score_df.head(10),
                    x=dimension_col,
                    y="Performance_Score",
                    text="Performance_Score",
                    title="Top Performing Products"
                )
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.dataframe(
                    score_df[[dimension_col, "Performance_Score"]],
                    use_container_width=True
                )




            



                






            

            


    # --- Smart Charts (Plotly) ---
    tab1, tab2, tab3 = st.tabs(["Categorical Analysis", "Trend Analysis", "Correlation"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            cat_dim = st.selectbox("Category", options=data_model.dimensions, key="cat_dim")
            cat_measure = st.selectbox("Measure", options=list(data_model.measures.keys()), key="cat_measure")
            unique_count = filtered_df[cat_dim].nunique()
            chart_type = st.radio("Type", ["Bar", "Pie", "Donut"], index=1 if unique_count < 5 else 0)

        with c2:
            chart_data = engine.get_grouping_data(filtered_df, cat_dim, cat_measure)
            if chart_type == "Bar":
                fig = px.bar(chart_data, x=cat_dim, y=cat_measure, title=f"{cat_measure} by {cat_dim}", text_auto='.2s', color=cat_measure)
            elif chart_type == "Pie":
                fig = px.pie(chart_data, names=cat_dim, values=cat_measure, title=f"{cat_measure} Distribution")
            else:
                fig = px.pie(chart_data, names=cat_dim, values=cat_measure, title=f"{cat_measure} Share", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if not data_model.date_fields:
            st.warning("No Date fields detected.")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                date_dim = st.selectbox("Date Field", options=data_model.date_fields, key="date_dim")
                trend_measure = st.selectbox("Metric", options=list(data_model.measures.keys()), key="trend_measure")
                trend_type = st.radio("Style", ["Line", "Area"], key="trend_type")

            with c2:
                trend_data = engine.get_grouping_data(filtered_df, date_dim, trend_measure)
                if trend_type == "Line":
                    fig = px.line(trend_data, x=date_dim, y=trend_measure, markers=True, title=f"{trend_measure} Over Time")
                else:
                    fig = px.area(trend_data, x=date_dim, y=trend_measure, title=f"{trend_measure} Accumulation")
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        sc1, sc2, sc3 = st.columns(3)
        with sc1: sc_x = st.selectbox("X-Axis", options=list(data_model.measures.keys()), index=0)
        with sc2: sc_y = st.selectbox("Y-Axis", options=list(data_model.measures.keys()), index=min(1, len(data_model.measures)-1))
        with sc3: sc_dim = st.selectbox("Dimension", options=data_model.dimensions, index=0)
        
        scatter_data, col_x, col_y = engine.get_scatter_data(filtered_df, sc_x, sc_y, sc_dim)
        fig = px.scatter(
            scatter_data, 
            x=col_x, 
            y=col_y, 
            color=sc_dim, 
            size=col_y, 
            hover_name=sc_dim, 
            title=f"{sc_x} vs {sc_y}")
        st.plotly_chart(fig, use_container_width=True)


    # --- Forecasting (Deep Learning / MLP) ---
    st.markdown("---")
    st.subheader("🔮 Smart Forecasting (Neural Network)")



# 🩺 DATA HEALTH GAUGE (Plotly)

if (
    "data_model" in st.session_state
    and st.session_state.data_model is not None
    and not filtered_df.empty
):
    try:
        dm = st.session_state.data_model
        analytics = AnalyticsEngine(filtered_df, dm)

        date_col = dm.date_fields[0]
        target_measure_name = (
            "Sales" if "Sales" in dm.measures
            else list(dm.measures.keys())[0]
        )

        health = analytics.compute_data_health(
            filtered_df,
            date_col,
            target_measure_name
        )

        score = health["score"]
        status = health["status"]

        # --- Two-column layout ---
        col_gauge, col_info = st.columns([1, 2])

        # -------------------------
        # LEFT: Compact Gauge
        # -------------------------
        with col_gauge:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={"suffix": " / 100", "font": {"size": 20}},
                    #title={"text": "🩺 Data Health", "font": {"size": 14}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 40], "color": "#ff4d4d"},
                            {"range": [40, 60], "color": "#ffa64d"},
                            {"range": [60, 80], "color": "#ffff66"},
                            {"range": [80, 100], "color": "#66ff66"},
                        ],
                        "threshold": {
                            "line": {"color": "black", "width": 3},
                            "value": score,
                        },
                    },
                )
            )

            fig_gauge.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=40, b=10),
            )

            st.plotly_chart(fig_gauge, use_container_width=True)

        # -------------------------
        # RIGHT: Details (Bullets)
        # -------------------------
        with col_info:
            st.markdown(
                f"""
                ### 🩺 Data Health Summary  
                **Score:** `{score} / 100`  
                **Status:** **{status}**

                • **Stability:** `{health['stability']}`  
                • **Seasonality:** `{health['seasonality']}`  
                • **Data Sufficiency:** `{health['sufficiency']}`  
                • **Forecasting:** `{ "Disabled" if score < 40 else "Enabled" }`
                """
            )

            if score < 40:
                st.warning(
                    "⚠️ Forecasting is disabled due to poor data health."
                )

        st.markdown("---")

    except Exception as e:
        st.error(f"🩺 Data Health error: {e}")


    
    if not data_model.date_fields:
        st.warning("Forecasting requires a Date column.")
    else:
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            forecast_date_col = st.selectbox("Date Field", options=data_model.date_fields, key="f_date")
            forecast_target = st.selectbox("Metric to Forecast", options=list(data_model.measures.keys()), key="f_target")
            horizon = st.slider("Months to Forecast", 1, 24, 6)
            generate_btn = st.button("Generate Forecast")

        with f_col2:
            if generate_btn:
                try:
                    with st.spinner("Training Neural Network (MLP) on your data..."):
                        forecaster = ForecastEngine(
                            filtered_df,
                            forecast_date_col,
                            data_model.measures[forecast_target]["column"]
                        )

                        result = forecaster.generate_forecast(horizon)

                        # -----------------------------
                        # FORECAST DISABLED CASE
                        # -----------------------------
                        if result[0] is None:
                            meta = result[3]

                            st.error("🚫 Forecasting Disabled")
                            st.info(
                                f"""
                                🔍 **Forecast Explainability**
                                - Confidence Level: {meta['confidence']}
                                - Reason: {meta['explanation']}
                                - Data Health Score: {meta['data_health']['score']}
                                - Status: {meta['data_health']['status']}
                                """
                            )
                            st.stop()   # ⬅ IMPORTANT: stop UI rendering here

                        # -----------------------------
                        # FORECAST ENABLED CASE
                        # -----------------------------
                        forecast_df, mae, smape_val, meta = result

                        m1, m2 = st.columns(2)
                        m1.metric("Avg Error (MAE)", f"{mae:,.2f}")
                        m2.metric("Error % (sMAPE)", f"{smape_val:.1f}%")




                        # ----------------------------------
# Forecast Explainability (STEP 4)
# ----------------------------------
                        st.info(
                            f"""
                            🔍 **Forecast Explainability**
                            - Model Used: {meta['model']}
                            - Data Points Used: {meta['data_points']}
                            - Confidence Level: {meta['confidence']}
                            - Interpretation: {meta['explanation']}
                            """
                        )

                        
                        
                        fig = px.line(forecast_df, x=forecast_date_col, y=data_model.measures[forecast_target]["column"], 
                                      color='Type', markers=True, title=f"Forecast: {forecast_target} ({horizon} Months)",
                                      color_discrete_map={"Historical": "blue", "Neural Net Forecast": "orange"})
                        fig.update_traces(patch={"line": {"dash": "dot"}}, selector={"legendgroup": "Neural Net Forecast"})
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Forecasting Error: {e}")
                    

    # =================================================
    # 🤖 CHAT ASSISTANT
    # =================================================
    st.markdown("---")
    
    # Define chat submission handler
    def submit_chat():
        user_input = st.session_state.chat_input_widget
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            chat_engine = ChatEngine(filtered_df)
            with st.spinner("Analyzing..."):
                response = chat_engine.generate_response(user_input)
            
            st.session_state.chat_history.append({"role": "ai", "content": response})
            st.session_state.chat_input_widget = "" # Clear input

    with st.expander("💬 AI Data Assistant", expanded=False):
        # 1. Display Chat History
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.write(f"**You:** {msg['content']}")
            else:
                st.write(f"**AI:** {msg['content']}")
        
        # 2. Input Area
        st.text_input(
            "Ask a question about your data...", 
            key="chat_input_widget", 
            on_change=submit_chat
        )

        

        