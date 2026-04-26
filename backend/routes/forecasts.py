from fastapi import APIRouter, Depends, status, HTTPException

from config.settings import settings
from src.models.forecast import ForecastCreate, ForecastOptionsRead, ForecastRead, Forecast
from src.services.forecast_service import ForecastService, get_forecast_service

from sqlmodel import Session, select
from database.session import get_session

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


@router.get("", response_model=list[Forecast], summary="List all forecasts")
def list_forecasts(session: Session = Depends(get_session)) -> list[Forecast]:
    return list(session.exec(select(Forecast)).all())


@router.get("/{forecast_id}", response_model=Forecast, summary="Get a forecast by ID")
def get_forecast(forecast_id: int, session: Session = Depends(get_session)) -> Forecast:
    forecast = session.get(Forecast, forecast_id)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found")
    return forecast


@router.get("/instrument/{instrument_id}", response_model=list[Forecast], summary="Get forecasts for an instrument")
def list_forecasts_by_instrument(instrument_id: int, session: Session = Depends(get_session)) -> list[Forecast]:
    return list(session.exec(select(Forecast).where(Forecast.instrument_id == instrument_id)).all())