# core/data_loader.py
import pandas as pd


class DataLoader:
    def load(self, uploaded_file):
        try:
            df = pd.read_csv(uploaded_file)
            return df
        except Exception as e:
            raise ValueError(f"Error loading dataset: {e}")
