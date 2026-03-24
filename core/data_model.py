from datetime import datetime


class DataModel:
    def __init__(
        self,
        dataset_name,
        row_count,
        column_count,
        columns,
        measures,
        dimensions,
        date_fields,
        ignored_columns,
    ):
        self.metadata = {
            "dataset_name": dataset_name,
            "row_count": row_count,
            "column_count": column_count,
            "created_at": datetime.now().isoformat(),
            "user_confirmed": True,
        }

        self.columns = columns
        self.measures = measures
        self.dimensions = dimensions
        self.date_fields = date_fields
        self.ignored_columns = ignored_columns

        self.rules = {
            "minimum_time_periods": 3,
            "allow_forecasting": len(date_fields) > 0,
        }
