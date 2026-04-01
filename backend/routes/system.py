from fastapi import APIRouter
from pydantic import BaseModel

from database.engine import ping_db


class HealthResponse(BaseModel):
    app_status: str
    db_status: str


router = APIRouter()


@router.get("/health", summary="Health check", description="Returns API and database status")
def read_health() -> HealthResponse:
    return HealthResponse(app_status="OK", db_status="OK" if ping_db() else "error")
