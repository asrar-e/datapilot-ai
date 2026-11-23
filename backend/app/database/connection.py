

from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)


def check_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one()


def initialize_database():
    """Create application metadata tables if they do not exist."""

    create_datasets_table = text("""
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id UUID PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            table_name VARCHAR(100) NOT NULL UNIQUE,
            file_type VARCHAR(10) NOT NULL,
            row_count BIGINT NOT NULL,
            column_count INTEGER NOT NULL,
            ingestion_status VARCHAR(30) NOT NULL,
            schema_json JSONB NOT NULL,
            profile_json JSONB NOT NULL,
            uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    create_uploaded_at_index = text("""
        CREATE INDEX IF NOT EXISTS idx_datasets_uploaded_at
        ON datasets (uploaded_at DESC);
    """)

    with engine.begin() as connection:
        connection.execute(create_datasets_table)
        connection.execute(create_uploaded_at_index)
