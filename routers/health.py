from fastapi import APIRouter
from sqlalchemy import text

from database import engine

router = APIRouter()


@router.get("/health", summary="Check API health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Check API and database readiness")
def readiness_check() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
