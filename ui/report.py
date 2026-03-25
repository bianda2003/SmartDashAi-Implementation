import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.analytics_engine import AnalyticsEngine
from core.forecast_engine import ForecastEngine
from core.chat_engine import ChatEngine

from core.ml_engine import (
    prepare_ml_data,
    check_data_health,
    evaluate_model,
    train_final_model
)


from core.analytics_engine import AnalyticsEngine


def render_report_stage():

    
    """
    STAGE 3 — ANALYTICS REPORT & DASHBOARD

    Responsibilities:
    - Apply interactive filters
    - Display KPI cards
    - Render categorical, trend & correlation charts
    - Provide YTD / MTD performance insights

    NOTE:
    - Forecasting, Data Health & Chat are handled separately
    """

    st.markdown("""
    <h1 id="top-title" style="margin:0; font-size:58px; font-weight:700;">
        <span style="color:#a855f7;">Smart</span>Dash<span style="color:#a855f7;">AI</span> <span style="color:#a855f7;">Report</span>
    </h1>

    <script>
    setTimeout(function() {
        window.scrollTo(0, 0);
    }, 100);
    </script>
    """, unsafe_allow_html=True)

    

    # ---------------------------------------------
    # Load session data
    # ---------------------------------------------
    df = st.session_state.df
    data_model = st.session_state.data_model

    engine = AnalyticsEngine(df, data_model)

    # =============================================
    # SIDEBAR — REPORT CONTROLS
    # =============================================
    active_filters = render_sidebar_controls(df, data_model)

    # Apply filters
    filtered_df = engine.apply_filters(active_filters)

    render_kpis(filtered_df, engine)

    render_time_performance(filtered_df, data_model)

    render_product_performance(filtered_df, data_model)

    st.markdown("---")

    render_smart_charts(filtered_df, engine, data_model)

    render_data_health(filtered_df, data_model)

    render_forecasting(filtered_df, data_model)

    render_chat_assistant(filtered_df)




# =================================================
# DATA HEALTH (Forecast Readiness)
# =================================================
def render_data_health(filtered_df, data_model):
    """
    Evaluates whether the dataset is suitable for forecasting
    based on stability, seasonality, and sufficiency.
    """

    if not data_model.date_fields or filtered_df.empty:
        st.warning("Data Health requires a Date field.")
        return

    analytics = AnalyticsEngine(filtered_df, data_model)

    date_col = data_model.date_fields[0]
    target_measure = (
        "Sales" if "Sales" in data_model.measures
        else list(data_model.measures.keys())[0]
    )

    try:
        health = analytics.compute_data_health(
            filtered_df,
            date_col,
            target_measure
        )

        score = health["score"]
        status = health["status"]

        st.subheader("Data Health")

        col_gauge, col_info = st.columns([1, 2])

        with col_gauge:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={"suffix": " / 100"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 40], "color": "#ff4d4d"},
                            {"range": [40, 60], "color": "#ffa64d"},
                            {"range": [60, 80], "color": "#ffff66"},
                            {"range": [80, 100], "color": "#66ff66"},
                        ],
                    },
                )
            )
            fig.update_layout(height=230, margin=dict(t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            st.markdown(
                f"""
                **Score:** `{score} / 100`  
                **Status:** **{status}**

                • Stability: `{health['stability']}`  
                • Seasonality: `{health['seasonality']}`  
                • Data Sufficiency: `{health['sufficiency']}`  
                • Forecasting: `{ "Disabled" if score < 40 else "Enabled" }`
                """
            )

            if score < 40:
                st.warning("⚠️ Forecasting disabled due to poor data quality.")

    except Exception as e:
        st.error(f"Data Health Error: {e}")

# =================================================
# FORECASTING (MLP + Explainability)
# =================================================
def render_forecasting(filtered_df, data_model):
    """
    Smart Forecasting with Accuracy Validation
    """

    st.markdown("---")
    st.subheader("Smart Forecasting")

    if not data_model.date_fields:
        st.warning("Forecasting requires a Date column.")
        return

    c1, c2 = st.columns([1, 2])

    with c1:
        date_col = st.selectbox(
            "Date Field",
            options=data_model.date_fields,
            key="forecast_date_field"
        )

        target = st.selectbox(
            "Metric to Forecast",
            options=list(data_model.measures.keys()),
            key="forecast_target_metric"
        )

        horizon = st.slider(
            "Months to Forecast",
            min_value=1,
            max_value=24,
            value=6
        )

        # ---------------------------------------
        # STEP 1: Accuracy Check (FIXED)
        # ---------------------------------------
        try:
            X, y = prepare_ml_data(
                filtered_df,
                data_model.measures[target]["column"]
            )

            health = check_data_health(X)

            if not health["valid"]:
                st.error(f"❌ {health['reason']}")
                return

            st.subheader("📊 Accuracy Check")

            acc_result = evaluate_model(X, y)

            st.write(f"Train Accuracy: {acc_result['train_acc']}%")
            st.write(f"Test Accuracy: {acc_result['test_acc']}%")
            st.write(f"R² Score: {acc_result['r2']}")

            # 🚨 Detect fake 100%
            if acc_result["test_acc"] > 98:
                st.warning("⚠️ Suspiciously high accuracy — possible low variance or leakage")

            if acc_result["overfit"]:
                st.warning("⚠️ Overfitting detected")
            else:
                st.success("✅ Model is reliable")

        except Exception as e:
            st.error(f"Accuracy Error: {e}")
            return

        # ---------------------------------------
        # STEP 2: Generate Button
        # ---------------------------------------
        generate = st.button("🚀 Generate Forecast")

    # ---------------------------------------
    # STEP 3: Forecast Execution
    # ---------------------------------------
    if generate:

        # 🚨 Block bad models
        if acc_result["test_acc"] < 60:
            st.error("❌ Forecast blocked due to low accuracy")
            return

        with c2:
            try:
                with st.spinner("Training Neural Network (MLP)..."):

                    forecaster = ForecastEngine(
                        filtered_df,
                        date_col,
                        data_model.measures[target]["column"]
                    )

                    result = forecaster.generate_forecast(horizon)

                    # -------- Forecast Disabled --------
                    if result[0] is None:
                        meta = result[3]
                        st.error("🚫 Forecasting Disabled")
                        st.info(
                            f"""
                            **Reason:** {meta['explanation']}  
                            **Confidence:** {meta['confidence']}  
                            **Data Health Score:** {meta['data_health']['score']}
                            """
                        )
                        return

                    # -------- Forecast Success --------
                    forecast_df, mae, smape_val, meta = result

                    m1, m2 = st.columns(2)
                    m1.metric("Avg Error (MAE)", f"{mae:,.2f}")
                    m2.metric("Error % (sMAPE)", f"{smape_val:.1f}%")

                    st.info(
                        f"""
                        **Model:** {meta['model']}  
                        **Data Points:** {meta['data_points']}  
                        **Confidence:** {meta['confidence']}  
                        **Explanation:** {meta['explanation']}
                        """
                    )

                    fig = px.line(
                        forecast_df,
                        x=date_col,
                        y=data_model.measures[target]["column"],
                        color="Type",
                        markers=True,
                        title=f"{target} Forecast ({horizon} Months)"
                    )

                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Forecasting Error: {e}")


# =================================================
# SIDEBAR CONTROLS
# =================================================
def render_sidebar_controls(df, data_model):
    st.sidebar.title("🛠️ Report Settings")

    # -------------------------------
    # KPI Selection
    # -------------------------------
    st.sidebar.subheader("1️ KPI Cards")

    valid_kpis = list(data_model.measures.keys())

    default_kpis = [
        k for k in valid_kpis
        if not any(x in k.lower() for x in ["ram", "weight", "inch", "battery"])
    ]

    if not default_kpis:
        default_kpis = valid_kpis[:4]

    selected_kpis = st.sidebar.multiselect(
        "Display Metrics",
        options=valid_kpis,
        default=default_kpis
    )

    st.session_state.selected_kpis = selected_kpis

    st.sidebar.markdown("---")

    # -------------------------------
    # Category Filters
    # -------------------------------
    st.sidebar.subheader("2️ Category Filters")
    filters = {}

    for dim in data_model.dimensions[:5]:
        options = sorted(df[dim].astype(str).unique())
        filters[dim] = st.sidebar.multiselect(dim, options)

    st.sidebar.markdown("---")

    # -------------------------------
    # Numeric Range Filters
    # -------------------------------
    st.sidebar.subheader("3️ Value Ranges")

    for measure in selected_kpis:
        col = data_model.measures[measure]["column"]

        if pd.api.types.is_numeric_dtype(df[col]):
            min_val, max_val = float(df[col].min()), float(df[col].max())

            if min_val < max_val:
                rng = st.sidebar.slider(
                    f"{measure} Range",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)
                )
                filters[f"{col}__range"] = rng

    if st.sidebar.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()

    return filters


# =================================================
# KPI RENDERING
# =================================================


def render_kpis(filtered_df, engine):
    st.markdown("---")
    selected_kpis = st.session_state.get("selected_kpis", [])

    if not selected_kpis:
        st.info("Select metrics from the sidebar to view KPIs.")
        return

    kpi_values = engine.compute_kpis(filtered_df)

    cols = st.columns(len(selected_kpis))
    for i, kpi in enumerate(selected_kpis):
        val = kpi_values.get(kpi, 0)
        cols[i].metric(kpi, f"{val:,.2f}")

# =================================================
# TIME INTELLIGENCE — YTD / MTD
# =================================================
def render_time_performance(filtered_df, data_model):
    """
    Renders YTD / MTD KPIs and YTD comparison chart
    """

    if not data_model.date_fields or filtered_df.empty:
        return

    date_col = data_model.date_fields[0]

    st.markdown("---")

    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        target_measure_name = st.selectbox(
            "Metric to evaluate (YTD/MTD)",
            options=list(data_model.measures.keys()),
            index=list(data_model.measures.keys()).index("Sales") if "Sales" in data_model.measures else 0,
            key="time_perf_measure"
        )
    
    measure_col = data_model.measures[target_measure_name]["column"]

    analytics = AnalyticsEngine(filtered_df, data_model)

    try:
        ytd = analytics.compute_ytd(filtered_df, date_col, measure_col)
        mtd = analytics.compute_mtd(filtered_df, date_col, measure_col)
        comp_df = analytics.compute_ytd_comparison(
            filtered_df, date_col, measure_col
        )

        st.subheader(f"📈 {target_measure_name} Performance")

        st.markdown("---")

        c1, c2, c3 = st.columns([1, 1, 2])
        
        

        with c1:
            st.metric(f"📆 YTD {target_measure_name}", f"{ytd:,.2f}")

        with c2:
            st.metric(f"🗓️ MTD {target_measure_name}", f"{mtd:,.2f}")

        with c3:
            if (
                comp_df is not None
                and not comp_df.empty
                and {"Month", "Year", "Value"}.issubset(comp_df.columns)
            ):
                fig = px.line(
                    comp_df,
                    x="Month",
                    y="Value",
                    color="Year",
                    markers=True,
                    title="YTD vs Previous Year"
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough historical data for YTD comparison.")

    except Exception as e:
        st.warning(f"Time performance skipped: {e}")


    # =================================================
# PRODUCT PERFORMANCE SCORE
# =================================================
def render_product_performance(filtered_df, data_model):
    """
    Computes and visualizes product performance using
    normalized business metrics (NO ML scoring).
    """

    st.markdown("---")
    st.subheader("🏆 Product Performance Score")

    if not data_model.dimensions or filtered_df.empty:
        st.info("No dimension available for performance analysis.")
        return

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        dimension = st.selectbox(
            "Product Category / Dimension",
            options=data_model.dimensions,
            index=data_model.dimensions.index("Product") if "Product" in data_model.dimensions else 0,
            key="product_perf_dim"
        )
    
    with c_sel2:
        valid_measures = [
            k for k, v in data_model.measures.items()
            if pd.api.types.is_numeric_dtype(filtered_df[v["column"]])
        ]
        if not valid_measures:
            st.info("No numeric measure available.")
            return

        target_measure = st.selectbox(
            "Performance Metric",
            options=valid_measures,
            index=valid_measures.index("Sales") if "Sales" in valid_measures else 0,
            key="product_perf_measure"
        )

    measure_col = data_model.measures[target_measure]["column"]

    # Aggregate
    agg = filtered_df.groupby(dimension)[measure_col].sum().reset_index()

    agg["Performance_Score"] = agg[measure_col].round(3)
    agg = agg.sort_values("Performance_Score", ascending=False)

    c1, c2 = st.columns([2, 1])

    with c1:
        fig = px.bar(
            agg.head(10),
            x=dimension,
            y="Performance_Score",
            text="Performance_Score",
            title="Top Performing Products"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.dataframe(
            agg[[dimension, "Performance_Score"]],
            use_container_width=True
        )




# =================================================
# SMART CHARTS
# =================================================
def render_smart_charts(df, engine, data_model):
    tab1, tab2, tab3 = st.tabs(
        ["📦 Categorical Analysis", "📈 Trend Analysis", "🔗 Correlation"]
    )

    # -------------------------------
    # CATEGORICAL ANALYSIS
    # -------------------------------
    with tab1:
        c1, c2 = st.columns([1, 2])

        with c1:
            dim = st.selectbox("Category", data_model.dimensions)
            measure = st.selectbox("Measure", list(data_model.measures.keys()))
            chart_type = st.radio("Chart Type", ["Bar", "Pie", "Donut"])

        with c2:
            chart_df = engine.get_grouping_data(df, dim, measure)

            if chart_type == "Bar":
                fig = px.bar(chart_df, x=dim, y=measure, text_auto=".2s")
            elif chart_type == "Pie":
                fig = px.pie(chart_df, names=dim, values=measure)
            else:
                fig = px.pie(chart_df, names=dim, values=measure, hole=0.4)

            st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # TREND ANALYSIS
    # -------------------------------
    with tab2:
        if not data_model.date_fields:
            st.warning("No date field available for trend analysis.")
            return

        c1, c2 = st.columns([1, 2])

        with c1:
            date_col = st.selectbox(
                "Date Field",
                data_model.date_fields,
                key="trend_date_field"
            )

            measure = st.selectbox("Metric", list(data_model.measures.keys()))
            style = st.radio("Style", ["Line", "Area"])

        with c2:
            trend_df = engine.get_grouping_data(df, date_col, measure)

            fig = (
                px.line(trend_df, x=date_col, y=measure, markers=True)
                if style == "Line"
                else px.area(trend_df, x=date_col, y=measure)
            )

            st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # CORRELATION ANALYSIS
    # -------------------------------
    with tab3:
        c1, c2, c3 = st.columns(3)

        with c1:
            x_metric = st.selectbox("X Axis", list(data_model.measures.keys()), index=0)
        with c2:
            y_metric = st.selectbox(
                "Y Axis",
                list(data_model.measures.keys()),
                index=min(1, len(data_model.measures) - 1),
            )
        with c3:
            dim = st.selectbox("Color By", data_model.dimensions)

        scatter_df, col_x, col_y = engine.get_scatter_data(
            df, x_metric, y_metric, dim
        )

        scatter_df["_point_size"] = scatter_df[col_y].abs()

        fig = px.scatter(
            scatter_df,
            x=col_x,
            y=col_y,
            color=dim,
            size="_point_size",
            hover_name=dim,
        )

        st.plotly_chart(fig, use_container_width=True)

        # =================================================
# AI DATA ASSISTANT
# =================================================
def render_chat_assistant(filtered_df):
    """
    Conversational interface for querying dataset insights.
    SAFE Streamlit state handling.
    """

    st.markdown("---")
    st.subheader("AI Data Assistant")

    # -----------------------------
    # Session state initialization
    # -----------------------------
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chat_buffer" not in st.session_state:
        st.session_state.chat_buffer = ""

    # -----------------------------
    # Submit handler
    # -----------------------------
    def submit_chat():
        user_input = st.session_state.chat_buffer.strip()

        if not user_input:
            return

        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        engine = ChatEngine(filtered_df)
        response = engine.generate_response(user_input)

        st.session_state.chat_history.append(
            {"role": "ai", "content": response}
        )

        # ✅ Clear INTERNAL buffer (NOT widget key)
        st.session_state.chat_buffer = ""

    # -----------------------------
    # UI
    # -----------------------------
    with st.expander("💬 Ask questions about your data"):
        for msg in st.session_state.chat_history:
            role = "You" if msg["role"] == "user" else "AI"
            st.write(f"**{role}:** {msg['content']}")

        st.text_input(
            "Ask a question...",
            key="chat_buffer"
        )

        st.button("Send", on_click=submit_chat)


