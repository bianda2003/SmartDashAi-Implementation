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

    st.title("📂 Import Data")
    st.markdown("Upload your dataset (CSV) to get started.")

    if st.button("Generate Multi-Year Sample Data"):
        generate_sample_data()
        return

    uploaded_file = st.file_uploader("Or choose a CSV file", type="csv")
    if uploaded_file:
        load_user_data(uploaded_file)

        


# -------------------------------------------------
# Helpers
# -------------------------------------------------

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
    Generates multi-year demo dataset for testing & demo purposes.
    """
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
        for _ in range(np.random.randint(3, 8)):
            product, category, unit_price, unit_cost = products[
                np.random.randint(len(products))
            ]

            qty = np.random.randint(1, 10)
            sales = qty * unit_price
            cost = qty * unit_cost

            rows.append({
                "Date": date,
                "Product": product,
                "Category": category,
                "Region": np.random.choice(regions),
                "Quantity": qty,
                "Unit_Price": unit_price,
                "Unit_Cost": unit_cost,
                "Sales_Amount": sales,
                "Cost_Amount": cost,
                "Profit": sales - cost,
            })

    df = pd.DataFrame(rows)

    profiler = DataProfiler()
    st.session_state.df = df
    st.session_state.profile_df = profiler.profile(df)
    st.session_state.app_stage = "model"
    st.rerun()
