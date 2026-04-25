from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from config.settings import settings
from database.session import get_session
from src.models.forecast import (
    Forecast,
    ForecastCreate,
    ForecastOptionsRead,
    ForecastRead,
)
from src.repositories.forecast_repository import forecast_repository
from src.repositories.instrument_repository import instrument_repository
from src.services.forecast_service import ForecastService, get_forecast_service

router = APIRouter(prefix="/forecasts")


@router.get(
    "/settings",
    response_model=ForecastOptionsRead,
    summary="Get forecast form settings",
)
def get_forecast_settings() -> ForecastOptionsRead:
    return ForecastOptionsRead(
        estimate_types=settings.forecast_options.estimate_types,
        scenarios=settings.forecast_options.scenarios,
    )


@router.post(
    "",
    response_model=ForecastRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a forecast",
)
def create_forecast(
    data: ForecastCreate,
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastRead:
    return service.create(data)


@router.get(
    "/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="Get stored forecasts for a ticker",
)
def get_forecasts(ticker: str, session: Session = Depends(get_session)) -> list[Forecast]:
    instrument = instrument_repository.get_by_ticker(session, ticker)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Instrument {ticker} not found"
        )

    return forecast_repository.get_by_instrument(session, instrument.id)
