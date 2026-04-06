# TODO: store predictions_fetch_date in Forecast model if needed for analysis
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from database.session import get_session
from src.models.forecast import Forecast
from src.repositories.forecast_repository import forecast_repository
from src.repositories.instrument_repository import instrument_repository
from src.services.yfinance_service import YFinanceService

router = APIRouter(prefix="/forecasts")

yfinance_service = YFinanceService()


@router.post(
    "/yfinance/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="Ingest yfinance data for a ticker",
)
def ingest_yfinance(ticker: str, session: Session = Depends(get_session)) -> dict:
    instrument = instrument_repository.get_by_ticker(session, ticker)
    if not instrument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Instrument {ticker} not found")

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
        forecast_repository.save(session, forecast)
        saved_forecasts += 1

    return {"ticker": ticker, "forecasts_saved": saved_forecasts}
