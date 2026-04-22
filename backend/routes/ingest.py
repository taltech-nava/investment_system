from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from database.session import get_session
from src.models.forecast import Forecast
from src.models.price import Price
from src.repositories.forecast_repository import forecast_repository
from src.repositories.instrument_repository import instrument_repository
from src.repositories.price_repository import price_repository
from src.services.yfinance_service import YFinanceService

router = APIRouter(prefix="/ingest")

yfinance_service = YFinanceService()


@router.post(
    "/yfinance/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="Ingest yfinance data for a ticker",
)
def ingest_yfinance(ticker: str, session: Session = Depends(get_session)) -> dict:
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
            extracted_raw_price=None,
            currency=instrument.currency,
        )
        forecast_repository.save(session, forecast)
        saved_forecasts += 1

    # Fetch and save realised closing price for today
    closing_price = yfinance_service.fetch_realised_price(ticker, date.today())
    saved_price = 0
    if closing_price is not None and not price_repository.get_by_instrument_and_date(
        session, instrument.id, date.today()
    ):
        price = Price(
            instrument_id=instrument.id,
            price_date=date.today(),
            price=closing_price,
            currency=instrument.currency,
            data_source="yfinance",
        )
        price_repository.save(session, price)
        saved_price = 1

    session.commit()
    return {"ticker": ticker, "forecasts_saved": saved_forecasts, "prices_saved": saved_price}
