
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from app.database.connection import engine
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.dataset_service import load_dataset


router = APIRouter(prefix="/datasets", tags=["Datasets"])

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"

MAX_FILE_SIZE = 25 * 1024 * 1024

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported."
        )

    # Read the uploaded file, with a size limit.
    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum upload size is 25 MB."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a safe storage filename.
    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        file_path.write_bytes(content)

        result = load_dataset(
            file_path=str(file_path),
            original_filename=Path(file.filename).name
        )

        return {
            "message": "Dataset uploaded successfully.",
            "dataset": result
        }

    except ValueError as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Dataset ingestion failed. Check backend logs."
        )
    
@router.get("")
def list_datasets():
    query = text("""
        SELECT
            dataset_id,
            dataset_name,
            original_filename,
            table_name,
            file_type,
            row_count,
            column_count,
            ingestion_status,
            uploaded_at
        FROM datasets
        ORDER BY uploaded_at DESC
    """)

    with engine.connect() as connection:
        results = connection.execute(query).mappings().all()

    return {
        "count": len(results),
        "datasets": [dict(row) for row in results],
    }


@router.get("/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str):

    query = text("""
        SELECT
            dataset_id,
            dataset_name,
            table_name,
            row_count,
            column_count,
            schema_json,
            profile_json,
            uploaded_at
        FROM datasets
        WHERE dataset_id = :dataset_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"dataset_id": dataset_id}
        ).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    return dict(result)