# core/ml_engine.py

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor


class MLEngine:
    def __init__(self, df, data_model):
        self.df = df
        self.model = data_model

    def prepare_data(self, target_column):
        df = self.df.copy()

        # Keep only numeric features
        numeric_df = df.select_dtypes(include="number")

        if target_column not in numeric_df.columns:
            raise ValueError("Selected target is not numeric")

        X = numeric_df.drop(columns=[target_column])
        y = numeric_df[target_column]

        if X.empty:
            raise ValueError("No numeric features available for training")

        return train_test_split(X, y, test_size=0.2, random_state=42)

    def train(self, target_column):
        X_train, X_test, y_train, y_test = self.prepare_data(target_column)

        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)

        return model, mae, r2

    def predict(self, model, X_latest):
        return model.predict(X_latest)[0]



# SMART FORECASTING

def prepare_ml_data(df, target):
    df = df.copy().dropna(subset=[target])

    # Try to find a date column to sort by
    date_cols = [c for c in df.columns if "date" in c.lower() or str(df[c].dtype).startswith("datetime")]
    if date_cols:
        main_date = date_cols[0]
        df[main_date] = pd.to_datetime(df[main_date], errors='coerce')
        df = df.dropna(subset=[main_date]).sort_values(by=main_date)

    y = df[target]
    X = df.drop(columns=[target])

    # Form time features on the date columns
    for col in date_cols:
        if col in X.columns:
            # We already converted the first date col, but need to be sure for others
            X[col] = pd.to_datetime(X[col], errors='coerce')

            X[col+"_year"] = X[col].dt.year
            X[col+"_month"] = X[col].dt.month
            X[col+"_day"] = X[col].dt.day
            X[col+"_dayofweek"] = X[col].dt.dayofweek

            X = X.drop(columns=[col])

    # Convert categorical → numeric
    X = pd.get_dummies(X, drop_first=True)

    return X, y



# HEALTH CHECK

def check_data_health(X):
    if len(X) < 30:
        return {"valid": False, "reason": "Too few rows"}

    if X.shape[1] == 0:
        return {"valid": False, "reason": "No features available"}

    return {"valid": True}



# EVALUATION 

def evaluate_model(X, y):

    # ✅ TIME-BASED SPLIT (NO SHUFFLE → NO LEAKAGE)
    split_index = int(len(X) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    # Avoid divide-by-zero
    mask_train = y_train != 0
    mask_test = y_test != 0

    train_acc = 100 - np.mean(
        np.abs((y_train[mask_train] - train_pred[mask_train]) / y_train[mask_train])
    ) * 100

    test_acc = 100 - np.mean(
        np.abs((y_test[mask_test] - test_pred[mask_test]) / y_test[mask_test])
    ) * 100

    # ✅ REAL METRIC
    r2 = r2_score(y_test, test_pred)

    return {
        "train_acc": round(train_acc, 2),
        "test_acc": round(test_acc, 2),
        "r2": round(r2, 3),
        "overfit": (train_acc - test_acc) > 10
    }


def train_final_model(X, y):
    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)
    return model