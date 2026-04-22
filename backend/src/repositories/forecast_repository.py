from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from datetime import date

from src.models.forecast import Forecast
from src.models.publisher import Publisher


class ForecastRepository:
    def save(self, session: Session, forecast: Forecast) -> Forecast:
        session.add(forecast)
        session.flush()
        return forecast

    def exists(
        self, session: Session, instrument_id: int, publisher_id: int, prediction_date: date
    ) -> bool:
        return (
            session.exec(
                select(Forecast).where(
                    Forecast.instrument_id == instrument_id,
                    Forecast.publisher_id == publisher_id,
                    Forecast.prediction_date == prediction_date,
                )
            ).first()
            is not None
        )

    def get_by_instrument(self, session: Session, instrument_id: int) -> list[Forecast]:
        return list(
            session.exec(
                select(Forecast)
                .where(Forecast.instrument_id == instrument_id)
                .order_by(Forecast.prediction_date.desc())
            ).all()
        )

    def get_or_create_publisher(self, session: Session, institution: str) -> Publisher:
        publisher = session.exec(
            select(Publisher).where(Publisher.institution == institution)
        ).first()
        if not publisher:
            publisher = Publisher(institution=institution)
            session.add(publisher)
            session.flush()  # assigns publisher.id without committing the transaction
        return publisher


forecast_repository = ForecastRepository()
