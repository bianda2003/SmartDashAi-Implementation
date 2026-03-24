# core/ml_engine.py
import pandas as pd
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
