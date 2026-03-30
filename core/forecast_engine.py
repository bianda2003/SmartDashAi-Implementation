import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

def smape(y_true, y_pred):
    y_true = np.array(y_true).reshape(-1)
    y_pred = np.array(y_pred).reshape(-1)
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    denominator = np.where(denominator == 0, 1, denominator)
    return np.mean(np.abs(y_true - y_pred) / denominator) * 100



class ForecastEngine:
    def __init__(self, df, date_col, target_col):
        self.df = df.copy()
        self.date_col = date_col
        self.target_col = target_col
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        # Increased look_back to capture more history (e.g., 6 months)
        self.look_back = 6 

    def prepare_data(self):
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col], errors="coerce")
        clean_df = self.df.dropna(subset=[self.date_col, self.target_col]).sort_values(self.date_col)

        # Monthly Aggregation
        ts_df = (
            clean_df
            .set_index(self.date_col)
            .resample("MS")[self.target_col]
            .sum()
            .reset_index()
        )
        
        # Feature Engineering 
        # Add Month and Year features to help the model learn seasonality
        ts_df['month'] = ts_df[self.date_col].dt.month
        ts_df['year_index'] = np.arange(len(ts_df)) # Helps capture long-term trend
        
        return ts_df

    def create_dataset(self, dataset, extra_features):
        X, y = [], []
        # Combine scaled target with temporal features
        for i in range(len(dataset) - self.look_back):
            # Window of past target values
            window = dataset[i:(i + self.look_back), 0]
            # Current temporal context (Month/Trend)
            context = extra_features[i + self.look_back] 
            
            X.append(np.concatenate([window, context]))
            y.append(dataset[i + self.look_back, 0])
        return np.array(X), np.array(y)

    def generate_forecast(self, months_to_forecast=6):
        ts_df = self.prepare_data()

        health = None


# DATA HEALTH GATING

        try:
            from core.analytics_engine import AnalyticsEngine

            analytics = AnalyticsEngine(self.df, None)
            health = analytics.compute_data_health(
                self.df,
                self.date_col,
                self.target_col
            )
        except Exception:
            health = None

            if health is not None and health["score"] < 40:
                return None, None, None, {
                    "model": "Neural Network (MLP)",
                    "data_points": len(ts_df),
                    "confidence": "Low",
                    "explanation": "Forecast disabled due to poor data health.",
                    "data_health": health
                }

        except Exception:
            pass

        data_points = len(ts_df)

        if data_points < (self.look_back + 4): # Increased threshold for better training
            return self._generate_fallback(ts_df, months_to_forecast)

        # Scale Target
        raw_values = ts_df[self.target_col].values.reshape(-1, 1)
        scaled_target = self.scaler.fit_transform(raw_values)
        
        # Prepare Temporal Features (Month is cyclical, so we scale it 1-12 -> 0-1)
        extra_features = ts_df[['month', 'year_index']].values
        feat_scaler = MinMaxScaler()
        scaled_features = feat_scaler.fit_transform(extra_features)

        X, y = self.create_dataset(scaled_target, scaled_features)

        # Train/Test Split
        split_idx = int(len(X) * 0.85)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # ENHANCEMENT: Optimized MLP Parameters
        model = MLPRegressor(
            hidden_layer_sizes=(100, 50), # Larger first layer
            activation="relu",
            solver="adam",
            alpha=0.001,           # L2 regularization to prevent overfitting
            learning_rate_init=0.01,
            max_iter=1000,
            early_stopping=True,   # Stop training when validation error stops improving
            validation_fraction=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)

        # ENHANCEMENT: Iterative Forecasting with Context ---
        future_predictions = []
        last_window = scaled_target[-self.look_back:].flatten()
        last_year_idx = scaled_features[-1, 1]
        
        for i in range(months_to_forecast):
            # Predict next month
            current_month = ((ts_df[self.date_col].max().month + i) % 12) + 1
            # Scale new context
            new_feat = feat_scaler.transform([[current_month, last_year_idx + (i+1)/len(ts_df)]])[0]
            
            input_vec = np.concatenate([last_window, new_feat]).reshape(1, -1)
            pred = model.predict(input_vec)
            
            future_predictions.append(pred[0])
            # Slide window: Remove oldest, add newest prediction
            last_window = np.append(last_window[1:], pred)

        # Inverse Scaling
        future_real_values = self.scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

        # Evaluation
        test_preds = model.predict(X_test)
        y_test_real = self.scaler.inverse_transform(y_test.reshape(-1, 1))
        test_preds_real = self.scaler.inverse_transform(test_preds.reshape(-1, 1))
        
        mae = mean_absolute_error(y_test_real, test_preds_real)
        smape_val = smape(y_test_real, test_preds_real)

        # Result Construction
        last_date = ts_df[self.date_col].max()
        future_dates = [last_date + pd.DateOffset(months=i + 1) for i in range(months_to_forecast)]
        
        future_df = pd.DataFrame({
            self.date_col: future_dates,
            self.target_col: future_real_values.flatten(),
            "Type": "Neural Net Forecast"
        })

        ts_df["Type"] = "Historical"
        combined_df = pd.concat([ts_df[[self.date_col, self.target_col, "Type"]], future_df])

  
        if smape_val > 25:
            confidence = "Low"
        elif smape_val > 15:
            confidence = "Medium"
        else:
            confidence = "High"

        explanation = "Based on model error."


        try:
            from core.analytics_engine import AnalyticsEngine
            analytics = AnalyticsEngine(self.df, None)

            volatility = analytics.compute_trend_volatility(
                self.df, self.date_col, self.target_col
            )

            if volatility is not None:
                if volatility > 0.6:
                    confidence = "Low"
                    explanation += " Historical data shows high volatility."
                elif volatility > 0.4 and confidence == "High":
                    confidence = "Medium"
                    explanation += " Some volatility detected in historical trend."
                else:
                    explanation += " Historical trend is stable."

        except Exception:
            pass


        metadata = {
            "model": "Neural Network (MLP) + Temporal Features",
            "data_points": data_points,
            "confidence": confidence,
            "explanation": explanation,
            "data_health": health
        }

        last_date = ts_df[self.date_col].max()
        future_dates = [last_date + pd.DateOffset(months=i + 1) for i in range(months_to_forecast)]
        
        future_df = pd.DataFrame({
            self.date_col: future_dates,
            self.target_col: future_real_values.flatten(),
            "Type": "Neural Net Forecast"
        })

        ts_df["Type"] = "Historical"
        combined_df = pd.concat([ts_df[[self.date_col, self.target_col, "Type"]], future_df])

        return combined_df, mae, smape_val, metadata
