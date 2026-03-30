import pandas as pd
import numpy as np

class AnalyticsEngine:
    def __init__(self, df, data_model):
        self.df = df
        self.model = data_model

    def apply_filters(self, filters):
        """
        Filters the DataFrame based on user selection.
        """
        df = self.df.copy()
        for col, values in filters.items():
            if col in df.columns and values:
                df = df[df[col].astype(str).isin(values)]
        return df

    def compute_kpis(self, df):
        kpis = {}
        for name, meta in self.model.measures.items():
            try:
                value = self._aggregate_measure(df, name)
                kpis[name] = None if pd.isna(value) else value
            except Exception:
                kpis[name] = None
        return kpis

    
    # CORE AGGREGATION LOGIC (INTERNAL)
  
    def _aggregate_measure(self, df, measure_name):
        """
        Helper to apply the correct aggregation based on model metadata.
        Supports Flow, Price (Weighted), Ratio, and Stock types.
        """
        if df.empty:
            return 0
            
        meta = self.model.measures.get(measure_name, {})
        m_type = meta.get("type", "flow")
        col = meta.get("column")

        if m_type == "flow":
            return df[col].sum()

        elif m_type == "price":
            w = meta.get("weight")
            if not w or w not in df.columns:
                return df[col].mean()
            return (df[col] * df[w]).sum() / df[w].sum()

        elif m_type == "ratio":
            num = meta.get("numerator")
            den = meta.get("denominator")
            if not num or not den:
                return 0
            return (df[num].sum() / df[den].sum()) * 100

        elif m_type == "score":
            return df[col].mean()

        elif m_type == "stock":
            date_col = self.model.date_fields[0]
            return df.sort_values(date_col)[col].iloc[-1]

        return df[col].sum()

   
    # TIME INTELLIGENCE METRICS
  
    def compute_ytd(self, df, date_col, measure_name):
        """Calculates Year-to-Date using dynamic aggregation."""
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        latest_date = df[date_col].max()
        
        if pd.isna(latest_date): 
            return 0

        ytd_df = df[(df[date_col].dt.year == latest_date.year) & (df[date_col] <= latest_date)]
        return self._aggregate_measure(ytd_df, measure_name)

    def compute_mtd(self, df, date_col, measure_name):
        """Calculates Month-to-Date using dynamic aggregation."""
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        latest_date = df[date_col].max()
        
        if pd.isna(latest_date): 
            return 0

        mtd_df = df[
            (df[date_col].dt.year == latest_date.year) & 
            (df[date_col].dt.month == latest_date.month) & 
            (df[date_col] <= latest_date)
        ]
        return self._aggregate_measure(mtd_df, measure_name)

   
    # PERIOD OVER PERIOD GROWTH (TREND)
  
    def compute_ytd_comparison(self, df, date_col, measure_name):
        """
        Calculates Monthly YTD vs Previous YTD for a true trend curve.
        Returns a melted DataFrame suitable for px.line(color='Year').
        """
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        latest_date = df[date_col].max()
        
        if pd.isna(latest_date):
            return pd.DataFrame()

        curr_year = latest_date.year
        prev_year = curr_year - 1
        measure_col = self.model.measures[measure_name]["column"]

        # Filter for current and previous years
        data_curr = df[df[date_col].dt.year == curr_year]
        data_prev = df[df[date_col].dt.year == prev_year]

        # Group by month and sum (standard for trend comparison)
        curr_monthly = data_curr.groupby(data_curr[date_col].dt.month)[measure_col].sum().reset_index()
        prev_monthly = data_prev.groupby(data_prev[date_col].dt.month)[measure_col].sum().reset_index()

        curr_monthly.columns = ["Month", "Current Year"]
        prev_monthly.columns = ["Month", "Previous Year"]

        # Merge and format for Plotly
        comparison_df = pd.merge(prev_monthly, curr_monthly, on="Month", how="outer").fillna(0)
        comparison_df = comparison_df.sort_values("Month")
        
        return comparison_df.melt(id_vars="Month", var_name="Year", value_name="Value")

   
    # GROUPING & VISUALIZATION DATA
  
    def get_grouping_data(self, df, dimension, measure):
        if dimension not in df.columns: 
            raise ValueError(f"Dimension '{dimension}' does not exist.")
        if measure not in self.model.measures: 
            raise ValueError(f"Measure '{measure}' not defined.")
            
        col_name = self.model.measures[measure]["column"]
        agg_type = self.model.measures[measure].get("aggregation", "sum")
        
        grouped = df.groupby(dimension, dropna=False)[col_name].agg(agg_type).reset_index()
        grouped.columns = [dimension, measure]
        
        if dimension in self.model.date_fields: 
            grouped = grouped.sort_values(dimension)
        else: 
            grouped = grouped.sort_values(measure, ascending=False)
        return grouped

    def get_scatter_data(self, df, measure_x, measure_y, dimension):
        """
        Prepares data for Scatter plots (Correlation analysis).
        Prevents DuplicateError by renaming columns.
        """
        if dimension not in df.columns:
            raise ValueError(f"Dimension '{dimension}' does not exist.")

        col_x_raw = self.model.measures[measure_x]["column"]
        col_y_raw = self.model.measures[measure_y]["column"]

        grouped = df.groupby(dimension)[[col_x_raw, col_y_raw]].sum().reset_index()

        name_x = f"{measure_x} (X)"
        name_y = f"{measure_y} (Y)"
        grouped.columns = [dimension, name_x, name_y]
        
        return grouped, name_x, name_y
  
    # CUMULATIVE TREND (YoY / MoM)
  
    def compute_cumulative_trend(self, df, date_col, measure_name):
        """
        Returns cumulative trend data with auto-switch:
        - YoY cumulative if >=2 years
        - MoM cumulative if only 1 year
        """
        if df.empty or date_col not in df.columns:
            return None, None

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        if df.empty:
            return None, None

        years = df[date_col].dt.year.unique()
        measure_col = self.model.measures[measure_name]["column"]

    
        # CASE 1: Year-over-Year
   
        if len(years) >= 2:
            df["Period"] = df[date_col].dt.month
            df["Year"] = df[date_col].dt.year

            grouped = (
                df.groupby(["Year", "Period"])[measure_col]
                .sum()
                .reset_index()
                .sort_values(["Year", "Period"])
            )

            grouped["Cumulative Value"] = (
                grouped.groupby("Year")[measure_col].cumsum()
            )

            return grouped, "YoY"

  
        # CASE 2: Month-over-Month

        df["Period"] = df[date_col].dt.to_period("M").astype(str)

        grouped = (
            df.groupby("Period")[measure_col]
            .sum()
            .reset_index()
            .sort_values("Period")
        )

        grouped["Cumulative Value"] = grouped[measure_col].cumsum()

        return grouped, "MoM"
    

    # CUMULATIVE TREND (AUTO YoY / MoM)

    def compute_cumulative_trend(self, df, date_col, measure_name):
        """
        Returns cumulative trend data with auto-switch:
        - YoY cumulative if >=2 years
        - MoM cumulative if only 1 year
        """
        if df.empty or date_col not in df.columns:
            return None, None

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        if df.empty:
            return None, None

        years = df[date_col].dt.year.unique()
        measure_col = self.model.measures[measure_name]["column"]

       
        # CASE 1: Year-over-Year
    
        if len(years) >= 2:
            df["Period"] = df[date_col].dt.month
            df["Year"] = df[date_col].dt.year

            grouped = (
                df.groupby(["Year", "Period"])[measure_col]
                .sum()
                .reset_index()
                .sort_values(["Year", "Period"])
            )

            grouped["Cumulative Value"] = (
                grouped.groupby("Year")[measure_col].cumsum()
            )

            return grouped, "YoY"

  
        # CASE 2: Month-over-Month

        df["Period"] = df[date_col].dt.to_period("M").astype(str)

        grouped = (
            df.groupby("Period")[measure_col]
            .sum()
            .reset_index()
            .sort_values("Period")
        )

        grouped["Cumulative Value"] = grouped[measure_col].cumsum()

        return grouped, "MoM"


    # TIME KPIs (YTD / MTD) — REUSES TREND LOGIC
   
    def compute_time_kpis(self, df, date_col, measure_name):
        """
        Returns YTD and MTD values using the same
        cumulative logic as trend charts.
        """
        trend_df, trend_type = self.compute_cumulative_trend(
            df, date_col, measure_name
        )

        if trend_df is None or trend_df.empty:
            return None, None


        # YoY case - use latest year

        if trend_type == "YoY":
            latest_year = trend_df["Year"].max()

            year_df = (
                trend_df[trend_df["Year"] == latest_year]
                .sort_values("Period")
            )

            ytd_value = year_df["Cumulative Value"].iloc[-1]

            if len(year_df) > 1:
                mtd_value = (
                    year_df["Cumulative Value"].iloc[-1]
                    - year_df["Cumulative Value"].iloc[-2]
                )
            else:
                mtd_value = ytd_value

            return ytd_value, mtd_value

        # MoM case → single year

        ytd_value = trend_df["Cumulative Value"].iloc[-1]

        if len(trend_df) > 1:
            mtd_value = (
                trend_df["Cumulative Value"].iloc[-1]
                - trend_df["Cumulative Value"].iloc[-2]
            )
        else:
            mtd_value = ytd_value

        return ytd_value, mtd_value
    


    # TREND STABILITY (0–1)

    def compute_trend_stability(self, df, date_col, measure_name):
        """
        Measures how stable period-to-period growth is.
        1.0 = very stable, 0.0 = highly volatile
        """
        trend_df, trend_type = self.compute_cumulative_trend(
            df, date_col, measure_name
        )

        if trend_df is None or trend_df.empty:
            return 0.0

        if trend_type == "YoY":
            deltas = []
            for _, g in trend_df.groupby("Year"):
                d = g.sort_values("Period")["Cumulative Value"].diff().dropna()
                deltas.extend(d.values)

            deltas = pd.Series(deltas)


        else:
            deltas = trend_df["Cumulative Value"].diff().dropna()

        if deltas.empty or deltas.mean() == 0:
            return 0.0

        volatility = deltas.std() / abs(deltas.mean())

        stability = 1 - min(volatility, 1.0)
        return round(stability, 3)
  

    def compute_seasonality_strength(self, df, date_col, measure_name):
        """
        Measures how strong repeating monthly patterns are.
        1.0 = strong seasonality, 0.0 = flat / random
        """
        if df.empty or date_col not in df.columns:
            return 0.0

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        if df.empty:
            return 0.0

        measure_col = self.model.measures[measure_name]["column"]

        df["Month"] = df[date_col].dt.month
        monthly_avg = df.groupby("Month")[measure_col].mean()

        if monthly_avg.mean() == 0:
            return 0.0

        strength = monthly_avg.std() / abs(monthly_avg.mean())

        return round(min(strength, 1.0), 3)


    # DATA SUFFICIENCY (0–1)

    def compute_data_sufficiency(self, df, date_col):
        """
        Measures if enough time periods exist for forecasting.
        """
        if df.empty or date_col not in df.columns:
            return 0.0

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        periods = df[date_col].dt.to_period("M").nunique()

        if periods < 6:
            return 0.2
        elif periods < 12:
            return 0.6
        else:
            return 1.0

    # DATA HEALTH SCORE 

    def compute_data_health(self, df, date_col, measure_name):
        """
        Combines stability, seasonality, and sufficiency
        into a single Data Health score.
        """
        stability = self.compute_trend_stability(df, date_col, measure_name)
        seasonality = self.compute_seasonality_strength(df, date_col, measure_name)
        sufficiency = self.compute_data_sufficiency(df, date_col)

        score = (
            50 * stability +
            30 * seasonality +
            20 * sufficiency
        )

        score = round(score, 1)

        if score >= 80:
            status = "Excellent"
        elif score >= 60:
            status = "Good"
        elif score >= 40:
            status = "Fair"
        else:
            status = "Poor"

        return {
            "score": score,
            "status": status,
            "stability": stability,
            "seasonality": seasonality,
            "sufficiency": sufficiency
        }


    def compute_trend_volatility(self, df, date_col, measure_name):
        """
        Measures volatility of cumulative trend.
        Returns a normalized volatility score (0–1).
        Lower = more stable trend.
        """
        trend_df, trend_type = self.compute_cumulative_trend(
            df, date_col, measure_name
        )

        if trend_df is None or trend_df.empty:
            return None

        # Use deltas (period-to-period change)
        deltas = trend_df["Cumulative Value"].diff().dropna()

        if deltas.empty or deltas.mean() == 0:
            return None

        volatility = deltas.std() / abs(deltas.mean())

        # Clamp into a reasonable range
        return round(min(volatility, 1.0), 3)

    
    