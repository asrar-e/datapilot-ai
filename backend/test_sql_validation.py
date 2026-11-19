
from app.agent.sql_validation_service import validate_sql

TABLE = "dataset_6d739646f7b1"

SCHEMA = [
    {"column_name": "region", "data_type": "text"},
    {"column_name": "quantity", "data_type": "integer"},
    {"column_name": "unit_price", "data_type": "numeric"}
]


def test_automatic_limit():

    sql = f"SELECT region FROM {TABLE}"

    result = validate_sql(sql, TABLE, SCHEMA)

    assert "LIMIT 1000" in result.upper()


def test_valid_aggregation():

    sql = f"""
    SELECT region,
           SUM(quantity * unit_price) AS total_revenue
    FROM {TABLE}
    GROUP BY region
    """

    result = validate_sql(sql, TABLE, SCHEMA)

    assert "LIMIT 1000" in result.upper()


def test_reject_wrong_table():

    sql = "SELECT region FROM unauthorized_table"

    try:
        validate_sql(sql, TABLE, SCHEMA)
        assert False, "Unauthorized table was accepted."
    except ValueError:
        pass


def test_reject_multiple_statements():

    sql = f"SELECT region FROM {TABLE}; SELECT region FROM {TABLE}"

    try:
        validate_sql(sql, TABLE, SCHEMA)
        assert False, "Multiple statements were accepted."
    except ValueError:
        pass


def test_reject_unknown_column():

    sql = f"SELECT password FROM {TABLE}"

    try:
        validate_sql(sql, TABLE, SCHEMA)
        assert False, "Unknown column was accepted."
    except ValueError:
        pass
