from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from datetime import date

from src.models.forecast import Forecast


class ForecastRepository:
    def save(self, session: Session, forecast: Forecast) -> Forecast:
        """Add and flush within the caller's transaction."""
        session.add(forecast)
        session.flush()
        return forecast

    def create(self, session: Session, forecast: Forecast) -> Forecast:
        """Add, commit, and refresh — used by ForecastService."""
        session.add(forecast)
        session.commit()
        session.refresh(forecast)
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


forecast_repository = ForecastRepository()
