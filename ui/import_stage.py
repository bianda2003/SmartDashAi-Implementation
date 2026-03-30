import streamlit as st
import pandas as pd
import numpy as np

from core.data_loader import DataLoader
from core.profiler import DataProfiler

def render_import_stage():
    """
    STAGE 1 — DATA IMPORT
    Responsibilities:
    - Upload user dataset OR generate demo data
    - Perform initial profiling
    - Transition to modeling stage
    """

    st.markdown("""
        <h1 style="font-size: 48px; margin-bottom: 6px;">
            📂 Import <span style="color: #a855f7;">DATA</span>
        </h1>
        """, unsafe_allow_html=True)

    st.markdown("""
        <p style="color: #cbd5e1; font-size: 16px;">
            Upload your dataset (CSV) to get started.
        </p>
        """, unsafe_allow_html=True)

    if st.button("Generate Multi-Year Sample Data"):
        generate_sample_data()
        return

    uploaded_file = st.file_uploader("Or choose a CSV file", type="csv")
    if uploaded_file:
        load_user_data(uploaded_file)

        #Helpers

def load_user_data(uploaded_file):
    """
    Loads CSV file, profiles data, and advances app state.
    """
    try:
        loader = DataLoader()
        df = loader.load(uploaded_file)

        profiler = DataProfiler()
        profile_df = profiler.profile(df)

        st.session_state.df = df
        st.session_state.profile_df = profile_df
        st.session_state.app_stage = "model"
        st.rerun()

    except Exception as e:
        st.error(f"Error loading file: {e}")


def generate_sample_data():
    """
    Generates realistic multi-year dataset with:
    - Seasonality
    - Noise
    - Multiple categories
    - Non-perfect patterns (prevents 100% accuracy)
    """

    import numpy as np
    import pandas as pd

    np.random.seed(42)

    dates = pd.date_range(start="2022-01-01", end="2024-12-31", freq="D")

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
        for _ in range(np.random.randint(3, 7)):

            product, category, base_price, base_cost = products[
                np.random.randint(len(products))
            ]

            region = np.random.choice(regions)

            # 🔥 SEASONALITY (monthly pattern)
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)

            # 🔥 RANDOM NOISE
            noise_factor = np.random.normal(1, 0.15)

            # 🔥 TREND (slow growth)
            trend_factor = 1 + (date.year - 2022) * 0.05

            qty = np.random.randint(1, 10)

            price = base_price * seasonal_factor * noise_factor * trend_factor
            cost = base_cost * seasonal_factor * noise_factor

            sales = qty * price
            cost_total = qty * cost
            profit = sales - cost_total

            rows.append({
                "Date": date,
                "Product": product,
                "Category": category,
                "Region": region,
                "Quantity": qty,
                "Unit_Price": round(price, 2),
                "Unit_Cost": round(cost, 2),
                "Sales": round(sales, 2),
                "Cost": round(cost_total, 2),
                "Profit": round(profit, 2),
            })

    df = pd.DataFrame(rows)

    # 👇 Keep your existing pipeline
    from core.profiler import DataProfiler

    profiler = DataProfiler()

    st.session_state.df = df
    st.session_state.profile_df = profiler.profile(df)
    st.session_state.app_stage = "model"

    st.success("✅ Realistic dataset generated (with noise & seasonality)")
    st.rerun()