import pandas as pd

class DataProfiler:
    def profile(self, df: pd.DataFrame):
        profile_rows = []
        total_rows = len(df)

        for col in df.columns:
            series = df[col]

            # Detect Type
            if pd.api.types.is_numeric_dtype(series):
                detected_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series) or "date" in col.lower():
                detected_type = "datetime"
            else:
                detected_type = "categorical"

            # Calculate Stats
            missing_count = series.isna().sum()
            missing_pct = round((missing_count / total_rows) * 100, 2)
            
            nunique = series.nunique()
            unique_pct = round(
                (nunique / total_rows) * 100 if total_rows > 0 else 0,
                2
            )

            profile_rows.append({
                "Column": col,
                "Detected Type": detected_type,
                "Missing %": missing_pct,
                "Unique %": unique_pct,
                "Unique Count": nunique
            })

        return pd.DataFrame(profile_rows)

    def recommend_drops(self, df, profile_df):
        """Recommends Columns to drop"""
        recommendations = {}
        for _, row in profile_df.iterrows():
            col = row["Column"]
            unique_pct = row["Unique %"]
            missing_pct = row["Missing %"]
            unique_count = row["Unique Count"]
            
            if missing_pct > 50:
                recommendations[col] = f"High missing values ({missing_pct}%)"
            elif unique_count <= 1:
                recommendations[col] = "Constant column (single value)"
            elif row["Detected Type"] == "categorical" and unique_pct > 95:
                recommendations[col] = "High cardinality (Unique > 95%)"
                
        return recommendations

    def detect_row_issues(self, df):
        """
        Detects removable rows (Duplicates & Nulls).
        Returns a dictionary of counts.
        """
        issues = {}
        
        # 1. Duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            issues["duplicates"] = dup_count
            
        # 2. Empty Rows (All Null)
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            issues["empty_rows"] = empty_rows
            
        # 3. Rows with ANY missing value (Optional strict cleaning)
        rows_with_nulls = df.isnull().any(axis=1).sum()
        if rows_with_nulls > 0:
             issues["rows_with_nulls"] = rows_with_nulls
             
        return issues