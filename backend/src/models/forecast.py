from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric, SmallInteger
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast_source import ForecastSource
    from .instrument import Instrument
    from .publisher import Publisher
    from .report import Report


class Forecast(SQLModel, table=True):
    __tablename__ = "forecasts"

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instruments.id", index=True)
    publisher_id: int = Field(foreign_key="publishers.id", index=True)

    prediction_date: date = Field(index=True)
    maturation_date: date = Field(index=True)
    horizon_source: str | None = Field(default=None, max_length=10)

    extracted_raw_price: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    extracted_raw_price_run: int | None = Field(
        default=None, sa_column=Column(SmallInteger, nullable=True)
    )
    extraction_status: str | None = Field(default=None, max_length=25)

    predicted_price: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    currency: str = Field(max_length=10)

    conviction: int | None = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    conviction_source: str | None = Field(default=None, max_length=10)
    method: str | None = Field(default=None, max_length=100)
    entry_mode: str | None = Field(default=None, max_length=20)

    estimate_type: str | None = Field(default=None, max_length=25)
    scenario: str | None = Field(default=None, max_length=10)

    instrument: Optional["Instrument"] = Relationship(back_populates="forecasts")
    publisher: Optional["Publisher"] = Relationship(back_populates="forecasts")
    reports: list["Report"] = Relationship(back_populates="forecast")
    forecast_sources: list["ForecastSource"] = Relationship(back_populates="forecast")
