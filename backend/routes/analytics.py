from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from database.session import get_session
from src.services.analytics_service import (
    AnalyticsService,
    DistributionResult,
    ReportsPageResult,
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


@router.get(
    "/reports",
    response_model=ReportsPageResult,
    summary="Get paginated report rows for analytics table",
)
def get_reports(
    ticker: str | None = None,
    publisher_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
    service: AnalyticsService = Depends(get_analytics_service),
    session: Session = Depends(get_session),
) -> ReportsPageResult:
    if ticker is not None and publisher_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide ticker or publisher_id, not both",
        )
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="page must be >= 1",
        )
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="page_size must be between 1 and 100",
        )

    return service.get_reports(
        session,
        ticker=ticker,
        publisher_id=publisher_id,
        page=page,
        page_size=page_size,
    )
