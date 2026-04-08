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
from src.services.price_prediction_service import price_prediction_service
from src.services.yfinance_service import YFinanceService

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

    # Fetch and save analyst price targets
    targets = yfinance_service.fetch_analyst_targets([ticker])
    saved_forecasts = 0
    for t in targets:
        publisher = forecast_repository.get_or_create_publisher(session, t["firm"])
        if forecast_repository.exists(session, instrument.id, publisher.id, t["grade_date"]):
            continue
        forecast = Forecast(
            instrument_id=instrument.id,
            publisher_id=publisher.id,
            prediction_date=t["grade_date"],
            maturation_date=t["maturation_date"],
            predicted_price=t["price_target"],
            extracted_raw_price=t["price_target"],  # same value until field is made nullable
            currency=instrument.currency,
        )

    return {"ticker": ticker, "forecasts_saved": saved_forecasts}

@router.post(
    "/predict/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="Run price prediction aggregation for a ticker",
)
def predict(ticker: str, session: Session = Depends(get_session)) -> dict:
    instrument = instrument_repository.get_by_ticker(session, ticker)
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Instrument {ticker} not found"
        )

    result = price_prediction_service.run(
        session=session,
        instrument_id=instrument.id,
        currency=instrument.currency,
    )

    if result["status"] == "no_data":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No source forecasts found for {ticker} within the last 365 days",
        )

    return result
