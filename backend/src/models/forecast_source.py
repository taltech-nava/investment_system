from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast import Forecast
    from .source import Source


class ForecastSource(SQLModel, table=True):
    """Junction table linking forecasts to the source documents they were extracted from."""

    __tablename__ = "forecast_sources"

    id: int | None = Field(default=None, primary_key=True)
    forecast_id: int = Field(foreign_key="forecasts.id", index=True)
    source_id: int = Field(foreign_key="sources.id", index=True)

    forecast: Optional["Forecast"] = Relationship(back_populates="forecast_sources")
    source: Optional["Source"] = Relationship(back_populates="forecast_sources")
