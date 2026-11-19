
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.query import router as query_router
from app.api.upload import router as upload_router
from app.core.config import APP_NAME
from app.database.connection import check_database_connection

app = FastAPI(
    title=APP_NAME,
    description="AI-powered natural language data analytics platform",
    version="0.1.0",
)

# Allow the local React development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {
        "application": APP_NAME,
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/health/database")
def database_health():
    try:
        result = check_database_connection()
        return {
            "database": "connected",
            "test_query_result": result,
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        )
