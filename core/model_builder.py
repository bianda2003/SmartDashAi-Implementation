from core.data_model import DataModel


class DataModelBuilder:
    def build(
        self,
        df,
        dataset_name,
        column_profile,
        measures,
        dimensions,
        date_fields,
        ignored_columns,
    ):
        columns_dict = {}

        for _, row in column_profile.iterrows():
            columns_dict[row["Column"]] = {
                "detected_type": row["Detected Type"],
                "missing_percentage": row["Missing %"],
                "unique_percentage": row["Unique %"],
            }

        return DataModel(
            dataset_name=dataset_name,
            row_count=df.shape[0],
            column_count=df.shape[1],
            columns=columns_dict,
            measures=measures,
            dimensions=dimensions,
            date_fields=date_fields,
            ignored_columns=ignored_columns,
        )
