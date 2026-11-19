
import re
import uuid
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    text,
    Date,
    DateTime,
    BigInteger,
    Float,
    Boolean,
    Text,
)

from app.services.profiling_service import profile_dataset
from app.database.connection import engine


def clean_column_names(columns):
    """Convert uploaded column names into PostgreSQL-friendly names."""

    cleaned = []
    used_names = set()

    for column in columns:
        name = str(column).strip().lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        name = name.strip("_")

        if not name:
            name = "column"

        name = name[:50]

        original_name = name
        counter = 1

        while name in used_names:
            name = f"{original_name}_{counter}"
            counter += 1

        used_names.add(name)
        cleaned.append(name)

    return cleaned


def infer_column_types(df):
    """
    Infer suitable PostgreSQL types from Pandas columns.

    Returns:
        df: DataFrame with date columns converted.
        sql_dtypes: SQLAlchemy types used by to_sql().
        schema: PostgreSQL-oriented schema metadata.
    """

    sql_dtypes = {}
    schema = []

    for column in df.columns:
        series = df[column]
        column_type = "TEXT"

        # 1. Attempt date detection for string/object columns.
        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            non_null = series.dropna()

            if not non_null.empty:
                sample = non_null.astype(str).str.strip()

                # Column names that suggest date/time information.
                date_name_hint = bool(
                    re.search(
                        r"(^|_)(date|datetime|timestamp|time)(_|$)",
                        column
                    )
                )

                # Recognize common date formats such as:
                # 2026-01-15, 15/01/2026, 2026-01-15 10:30:00
                date_pattern = sample.str.match(
                    r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}"
                )

                looks_like_date = (
                    date_name_hint
                    or date_pattern.mean() >= 0.80
                )

                if looks_like_date:
                    parsed = pd.to_datetime(
                        series,
                        errors="coerce",
                        format="mixed"
                    )

                    valid_ratio = parsed.notna().sum() / len(non_null)

                    # Require at least 95% successful conversions.
                    if (
                        valid_ratio >= 0.95
                        and pd.api.types.is_datetime64_any_dtype(parsed)
                    ):
                        has_time = sample.str.contains(
                            r"[T ]\d{1,2}:\d{2}",
                            regex=True
                        ).any()

                        if has_time:
                            df[column] = parsed

                            if isinstance(parsed.dtype, pd.DatetimeTZDtype):
                                sql_dtypes[column] = DateTime(
                                    timezone=True
                                )
                                column_type = "TIMESTAMP WITH TIME ZONE"
                            else:
                                sql_dtypes[column] = DateTime()
                                column_type = "TIMESTAMP"

                        else:
                            df[column] = parsed.dt.date
                            sql_dtypes[column] = Date()
                            column_type = "DATE"

        # 2. Infer numeric and Boolean types.
        if column_type == "TEXT":

            if pd.api.types.is_bool_dtype(df[column]):
                sql_dtypes[column] = Boolean()
                column_type = "BOOLEAN"

            elif pd.api.types.is_integer_dtype(df[column]):
                sql_dtypes[column] = BigInteger()
                column_type = "BIGINT"

            elif pd.api.types.is_numeric_dtype(df[column]):
                sql_dtypes[column] = Float()
                column_type = "DOUBLE PRECISION"

            else:
                sql_dtypes[column] = Text()
                column_type = "TEXT"

        schema.append({
            "column_name": column,
            "data_type": column_type
        })

    return df, sql_dtypes, schema


def load_dataset(file_path: str, original_filename: str):
    """Read, profile and load an uploaded dataset into PostgreSQL."""

    file_extension = Path(original_filename).suffix.lower()

    # 1. Read the uploaded file.
    if file_extension == ".csv":
        df = pd.read_csv(file_path)

    elif file_extension == ".xlsx":
        df = pd.read_excel(file_path, engine="openpyxl")

    else:
        raise ValueError("Only CSV and XLSX files are supported.")

    # 2. Validate the dataset.
    if df.empty:
        raise ValueError("The uploaded dataset contains no records.")

    if len(df.columns) == 0:
        raise ValueError("The uploaded dataset has no columns.")

    # 3. Clean column names.
    df.columns = clean_column_names(df.columns)

    # 4. Infer data types before profiling and loading.
    df, sql_dtypes, schema = infer_column_types(df)

    # 5. Generate dataset profile using converted values.
    profile = profile_dataset(df)

    # 6. Generate unique dataset identifiers.
    dataset_id = uuid.uuid4()
    table_name = f"dataset_{uuid.uuid4().hex[:12]}"

    dataset_name = Path(original_filename).stem

    row_count = len(df)
    column_count = len(df.columns)

    # 7. Load data and register metadata transactionally.
    with engine.begin() as connection:

        df.to_sql(
            name=table_name,
            con=connection,
            if_exists="fail",
            index=False,
            chunksize=1000,
            dtype=sql_dtypes
        )

        connection.execute(
            text("""
                INSERT INTO datasets (
                    dataset_id,
                    dataset_name,
                    original_filename,
                    table_name,
                    file_type,
                    row_count,
                    column_count,
                    ingestion_status,
                    schema_json,
                    profile_json
                )
                VALUES (
                    :dataset_id,
                    :dataset_name,
                    :original_filename,
                    :table_name,
                    :file_type,
                    :row_count,
                    :column_count,
                    :status,
                    CAST(:schema_json AS jsonb),
                    CAST(:profile_json AS jsonb)
                )
            """),
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "original_filename": original_filename,
                "table_name": table_name,
                "file_type": file_extension.replace(".", ""),
                "row_count": row_count,
                "column_count": column_count,
                "status": "completed",
                "schema_json": json.dumps(schema),
                "profile_json": json.dumps(profile)
            }
        )

    return {
        "dataset_id": str(dataset_id),
        "dataset_name": dataset_name,
        "table_name": table_name,
        "row_count": row_count,
        "column_count": column_count,
        "columns": list(df.columns),
        "status": "completed"
    }
