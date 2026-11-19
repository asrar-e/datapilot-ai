
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder

from app.database.connection import engine
from app.agent.sql_validation_service import validate_sql


def execute_dataset_query(
    sql: str,
    table_name: str,
    schema: list
):
    """
    Validate and execute a dataset query in a read-only transaction.
    """

    # 1. Validate before touching the database
    safe_sql = validate_sql(
        sql=sql,
        expected_table=table_name,
        schema=schema
    )

    # 2. Start a database transaction
    with engine.connect() as connection:

        transaction = connection.begin()

        try:
            # Prevent database modifications in this transaction
            connection.execute(
                text("SET TRANSACTION READ ONLY")
            )

            # Stop queries that run longer than five seconds
            connection.execute(
                text("SET LOCAL statement_timeout = '5000ms'")
            )

            # 3. Execute the validated query
            result = connection.execute(
                text(safe_sql)
            )

            rows = [
                dict(row)
                for row in result.mappings().all()
            ]

            columns = list(result.keys())

            transaction.commit()

            # 4. Convert dates and decimals into JSON-compatible values
            rows = jsonable_encoder(rows)

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "executed_sql": safe_sql
            }

        except Exception:
            transaction.rollback()
            raise
