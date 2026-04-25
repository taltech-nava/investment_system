from __future__ import annotations

from sqlmodel import Session

from src.models.forecast import Forecast


class ForecastRepository:
    def create(self, session: Session, forecast: Forecast) -> Forecast:
        session.add(forecast)
        session.commit()
        session.refresh(forecast)
        return forecast


forecast_repository = ForecastRepository()
