from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # noqa: TC002

from database.session import get_session
from src.models.forecast import Forecast  # noqa: TC001
from src.repositories.forecast_repository import forecast_repository
from src.repositories.instrument_repository import instrument_repository

router = APIRouter(prefix="/forecasts")


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
