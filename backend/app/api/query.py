
import logging

logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database.connection import engine
from app.agent.sql_generation_service import generate_sql
from app.services.query_execution_service import execute_dataset_query

router = APIRouter(prefix="/datasets", tags=["AI Query"])
class ExecuteQueryRequest(BaseModel):
    sql: str = Field(
        min_length=5,
        max_length=10000,
        description="SQL query to validate and execute."
    )

class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="A natural-language question about the uploaded dataset."
    )


@router.post("/{dataset_id}/generate-sql")
def generate_dataset_sql(
    dataset_id: str,
    request: QueryRequest
):
    # 1. Find the dataset and its schema
    query = text("""
        SELECT
            table_name,
            schema_json
        FROM datasets
        WHERE dataset_id = :dataset_id
    """)

    with engine.connect() as connection:
        dataset = connection.execute(
            query,
            {"dataset_id": dataset_id}
        ).mappings().first()

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # 2. Ask Gemini to generate SQL
    try:
        result = generate_sql(
            question=request.question,
            table_name=dataset["table_name"],
            schema=dataset["schema_json"]
        )

        return {
            "dataset_id": dataset_id,
            "question": request.question,
            "generated_query": result
        }

    
    except Exception as error:
        logger.exception("Gemini SQL generation failed")

        raise HTTPException(
            status_code=502,
            detail=f"SQL generation failed: {str(error)}"
        )
    
@router.post("/{dataset_id}/execute-sql")
def execute_sql_endpoint(
    dataset_id: str,
    request: ExecuteQueryRequest
):
    # 1. Retrieve the dataset's table and schema
    query = text("""
        SELECT table_name, schema_json
        FROM datasets
        WHERE dataset_id = :dataset_id
    """)

    with engine.connect() as connection:
        dataset = connection.execute(
            query,
            {"dataset_id": dataset_id}
        ).mappings().first()

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # 2. Validate and execute the query
    try:
        result = execute_dataset_query(
            sql=request.sql,
            table_name=dataset["table_name"],
            schema=dataset["schema_json"]
        )

        return {
            "dataset_id": dataset_id,
            "status": "success",
            "result": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("Dataset SQL execution failed")

        raise HTTPException(
            status_code=500,
            detail="SQL execution failed. Check backend logs."
        )

@router.post("/{dataset_id}/ask")
def ask_dataset_question(
    dataset_id: str,
    request: QueryRequest
):
    """
    Complete analytics workflow:
    Natural language -> SQL generation -> validation -> execution.
    """

    # 1. Retrieve dataset metadata
    query = text("""
        SELECT table_name, schema_json
        FROM datasets
        WHERE dataset_id = :dataset_id
    """)

    with engine.connect() as connection:
        dataset = connection.execute(
            query,
            {"dataset_id": dataset_id}
        ).mappings().first()

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    # 2. Generate SQL using Groq
    try:
        generated_query = generate_sql(
            question=request.question,
            table_name=dataset["table_name"],
            schema=dataset["schema_json"]
        )

        generated_sql = generated_query.get("sql")

        if not isinstance(generated_sql, str) or not generated_sql.strip():
            raise ValueError("The model did not generate valid SQL.")

    except Exception:
        logger.exception("SQL generation failed")

        raise HTTPException(
            status_code=502,
            detail="AI SQL generation failed. Check backend logs."
        )

    # 3. Validate and execute generated SQL
    try:
        execution_result = execute_dataset_query(
            sql=generated_sql,
            table_name=dataset["table_name"],
            schema=dataset["schema_json"]
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"SQL validation failed: {str(error)}"
        )

    except Exception:
        logger.exception("SQL execution failed")

        raise HTTPException(
            status_code=500,
            detail="SQL execution failed. Check backend logs."
        )

    # 4. Return complete analytics response
    return {
        "dataset_id": dataset_id,
        "question": request.question,
        "status": "success",
        "generated_query": generated_query,
        "result": execution_result
    }
