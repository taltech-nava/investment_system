from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast import Forecast
    from .forecast_aggregate import ForecastAggregate


class AggregateComponent(SQLModel, table=True):
    __tablename__ = "aggregate_components"

    id: int | None = Field(default=None, primary_key=True)
    aggregate_id: int = Field(foreign_key="forecast_aggregates.id", index=True)
    forecast_id: int = Field(foreign_key="forecasts.id", index=True)

    aggregate: Optional["ForecastAggregate"] = Relationship(back_populates="components")
    forecast: Optional["Forecast"] = Relationship(back_populates="aggregate_components")
