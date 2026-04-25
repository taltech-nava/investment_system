from datetime import date

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from database.session import get_session
from src.models.forecast import Forecast, ForecastCreate, ForecastRead
from src.models.instrument import Instrument
from src.repositories.forecast_repository import forecast_repository
from src.services.publisher_service import PublisherService


class ForecastService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.publisher_service = PublisherService(session)

    def create(self, data: ForecastCreate) -> ForecastRead:
        instrument = self.session.get(Instrument, data.instrument_id)
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found"
            )

        publisher = self.publisher_service.get_or_create(data.publisher_name)

        forecast = Forecast(
            instrument_id=data.instrument_id,
            publisher_id=publisher.id,
            prediction_date=date.today(),
            maturation_date=data.maturation_date,
            predicted_price=data.predicted_price,
            currency=instrument.currency,
            conviction=data.conviction,
            conviction_source=data.conviction_source,
            horizon_source=data.horizon_source,
            method=data.method,
            entry_mode=data.entry_mode,
            estimate_type=data.estimate_type,
            scenario=data.scenario,
        )

        created = forecast_repository.create(self.session, forecast)
        return ForecastRead.model_validate(created)


def get_forecast_service(session: Session = Depends(get_session)) -> ForecastService:
    return ForecastService(session)
