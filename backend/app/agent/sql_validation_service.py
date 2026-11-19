
import sqlglot
from sqlglot import exp


MAX_ROWS = 1000


def validate_sql(
    sql: str,
    expected_table: str,
    schema: list
) -> str:
    """
    Validate AI-generated SQL before PostgreSQL execution.
    Only one SELECT query against the requested dataset is allowed.
    """

    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    # 1. Parse all statements and reject multiple statements
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as error:
        raise ValueError(f"Invalid SQL syntax: {error}")

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    parsed = statements[0]

    # 2. Allow only SELECT
    if not isinstance(parsed, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    # 3. Reject nested queries and complex constructs
    if len(list(parsed.find_all(exp.Select))) != 1:
        raise ValueError("Nested SELECT queries are not allowed.")

    if parsed.find(exp.Join):
        raise ValueError("JOIN operations are not allowed.")

    if parsed.find(exp.Subquery) or parsed.find(exp.CTE):
        raise ValueError("Subqueries and CTEs are not allowed.")

    if parsed.args.get("into"):
        raise ValueError("SELECT INTO is not allowed.")

    if parsed.args.get("locks"):
        raise ValueError("Locking clauses are not allowed.")

    # 4. Validate referenced table
    tables = list(parsed.find_all(exp.Table))

    if len(tables) != 1:
        raise ValueError("Query must reference exactly one table.")

    table = tables[0]

    if table.name.lower() != expected_table.lower():
        raise ValueError("Query references an unauthorized table.")

    if table.db or table.catalog:
        raise ValueError("Schema-qualified table references are not allowed.")

    # 5. Build allowed column names
    allowed_columns = {
        column["column_name"].lower()
        for column in schema
    }

    aliases = {
        projection.alias.lower()
        for projection in parsed.expressions
        if isinstance(projection, exp.Alias)
    }

    allowed_columns.update(aliases)

    table_alias = table.alias.lower() if table.alias else ""

    # 6. Validate referenced columns
    for column in parsed.find_all(exp.Column):

        column_name = column.name.lower()

        if column_name == "*":
            continue

        if column_name not in allowed_columns:
            raise ValueError(
                f"Unknown or unauthorized column: {column_name}"
            )

        if column.table:
            if column.table.lower() not in {
                table.name.lower(),
                table_alias
            }:
                raise ValueError("Unauthorized table alias.")

   
    # 7. Enforce maximum result rows
    limit = parsed.args.get("limit")

    if limit is None:
        parsed.set(
            "limit",
            exp.Limit(
                expression=exp.Literal.number(MAX_ROWS)
            )
        )
    else:
        limit_value = limit.expression

        if not isinstance(limit_value, exp.Literal):
            raise ValueError("LIMIT must be a numeric literal.")

        if not limit_value.is_int:
            raise ValueError("LIMIT must be an integer.")

        requested_limit = int(limit_value.this)

        if requested_limit <= 0:
            raise ValueError("LIMIT must be greater than zero.")

        if requested_limit > MAX_ROWS:
            parsed.set(
                "limit",
                exp.Limit(
                    expression=exp.Literal.number(MAX_ROWS)
                )
            )


    # 8. Return normalized PostgreSQL SQL
    return parsed.sql(dialect="postgres")
