from fastapi import APIRouter, Depends, status

from config.settings import settings
from src.models.forecast import ForecastCreate, ForecastOptionsRead, ForecastRead
from src.services.forecast_service import ForecastService, get_forecast_service

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
