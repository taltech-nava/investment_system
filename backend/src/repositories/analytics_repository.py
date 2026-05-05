from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlmodel import select

from src.models.forecast import Forecast
from src.models.instrument import Instrument
from src.models.publisher import Publisher
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

    def get_report_rows(
        self,
        session: Session,
        *,
        ticker: str | None,
        publisher_id: int | None,
        offset: int,
        limit: int,
    ) -> list[tuple[Report, Forecast, Instrument, Publisher]]:
        query = (
            select(Report, Forecast, Instrument, Publisher)
            .join(Forecast, Report.forecast_id == Forecast.id)
            .join(Instrument, Forecast.instrument_id == Instrument.id)
            .join(Publisher, Forecast.publisher_id == Publisher.id)
        )

        if ticker is not None:
            query = query.where(Instrument.ticker == ticker.upper())
        elif publisher_id is not None:
            query = query.where(Forecast.publisher_id == publisher_id)

        query = query.order_by(Report.review_date.desc(), Report.id.desc()).offset(offset).limit(limit)
        return list(session.exec(query).all())

    def get_report_rows_count(
        self,
        session: Session,
        *,
        ticker: str | None,
        publisher_id: int | None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Report)
            .join(Forecast, Report.forecast_id == Forecast.id)
            .join(Instrument, Forecast.instrument_id == Instrument.id)
        )

        if ticker is not None:
            query = query.where(Instrument.ticker == ticker.upper())
        elif publisher_id is not None:
            query = query.where(Forecast.publisher_id == publisher_id)

        return int(session.exec(query).one())


analytics_repository = AnalyticsRepository()
