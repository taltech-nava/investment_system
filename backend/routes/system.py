from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


router = APIRouter()


@router.get("/health", summary="Health check", description="Returns API status")
def read_health() -> HealthResponse:
    return HealthResponse(status="OK")
