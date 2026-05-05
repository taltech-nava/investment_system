from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from database.session import get_session
from src.services.analytics_service import (
    AnalyticsService,
    DistributionResult,
    get_analytics_service,
)

router = APIRouter(prefix="/analytics")


@router.get(
    "/distribution",
    response_model=DistributionResult,
    summary="Get prediction error distribution",
)
def get_distribution(
    ticker: str | None = None,
    publisher_id: int | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
    session: Session = Depends(get_session),
) -> DistributionResult:
    if ticker is not None and publisher_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide ticker or publisher_id, not both",
        )
    return service.get_distribution(session, ticker=ticker, publisher_id=publisher_id)
