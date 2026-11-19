
import pandas as pd


def profile_dataset(df: pd.DataFrame):
    """
    Generate schema information and basic data-quality metrics.
    """

    columns = []

    for column in df.columns:

        series = df[column]

        column_profile = {
            "name": column,
            "type": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique()),
            "sample_values": [
                str(value)
                for value in series.dropna().head(5).tolist()
            ]
        }

        # Add numerical statistics only to numeric columns.
        if pd.api.types.is_numeric_dtype(series):

            column_profile["statistics"] = {
                "minimum": float(series.min())
                if series.notna().any() else None,

                "maximum": float(series.max())
                if series.notna().any() else None,

                "average": float(series.mean())
                if series.notna().any() else None
            }

        columns.append(column_profile)

    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns
    }

    return profile
