from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import select

from src.models.forecast import Forecast
from src.models.instrument import Instrument
from src.models.report import Report

if TYPE_CHECKING:
    from sqlmodel import Session


class AnalyticsRepository:
    def get_all_errors(self, session: Session) -> list[float]:
        return [float(r) for r in session.exec(select(Report.price_return_error)).all()]

    def get_errors_by_ticker(self, session: Session, ticker: str) -> list[float]:
        rows = session.exec(
            select(Report.price_return_error)
            .join(Forecast, Report.forecast_id == Forecast.id)
            .join(Instrument, Forecast.instrument_id == Instrument.id)
            .where(Instrument.ticker == ticker.upper())
        ).all()
        return [float(r) for r in rows]

    def get_errors_by_publisher(self, session: Session, publisher_id: int) -> list[float]:
        rows = session.exec(
            select(Report.price_return_error)
            .join(Forecast, Report.forecast_id == Forecast.id)
            .where(Forecast.publisher_id == publisher_id)
        ).all()
        return [float(r) for r in rows]


analytics_repository = AnalyticsRepository()
