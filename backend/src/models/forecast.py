from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from pydantic import field_validator, model_validator
from sqlalchemy import CheckConstraint, Column, Numeric, SmallInteger
from sqlmodel import Field, Relationship, SQLModel

from config.settings import settings

PREDICTED_PRICE_MAX = Decimal("99999999.9999")

if TYPE_CHECKING:
    from .aggregate_component import AggregateComponent
    from .forecast_source import ForecastSource
    from .instrument import Instrument
    from .publisher import Publisher
    from .report import Report


class Forecast(SQLModel, table=True):
    __tablename__ = "forecasts"
    __table_args__ = (
        CheckConstraint(
            "estimate_type IN ('source_point_estimate', 'llm_point_estimate', 'llm_scenario_estimate', 'manual_point_estimate', 'manual_scenario_estimate')",
            name="chk_forecast_estimate_type",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instruments.id", index=True)
    publisher_id: int = Field(foreign_key="publishers.id", index=True)

    prediction_date: date = Field(index=True)
    maturation_date: date = Field(index=True)
    horizon_source: str | None = Field(default=None, max_length=30)

    extracted_raw_price: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 4), nullable=True)
    )
    extracted_raw_price_run: int | None = Field(
        default=None, sa_column=Column(SmallInteger, nullable=True)
    )
    extraction_status: str | None = Field(default=None, max_length=25)

    predicted_price: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(12, 4), nullable=True)
    )
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
<<<<<<< HEAD


class ForecastCreate(SQLModel):
    instrument_id: int = Field(gt=0)
    scenario: str = Field(max_length=10)
    predicted_price: Decimal = Field(
        gt=0,
        le=PREDICTED_PRICE_MAX,
        max_digits=12,
        decimal_places=4,
    )
    maturation_date: date
    publisher_name: str | None = Field(default=None, max_length=255)
    conviction: int = Field(default=3, ge=1, le=5)
    conviction_source: str = Field(max_length=10)
    horizon_source: str = Field(max_length=30)
    method: str | None = Field(default=None, max_length=100)
    entry_mode: str = Field(max_length=20)
    estimate_type: str = Field(max_length=25)

    @field_validator("maturation_date")
    @classmethod
    def maturation_date_must_be_future(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("maturation date must be in the future")
        return v

    @field_validator(
        "scenario",
        "conviction_source",
        "horizon_source",
        "entry_mode",
        "estimate_type",
    )
    @classmethod
    def required_string_fields_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field cannot be blank")
        return normalized

    @field_validator("method", "publisher_name")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_supported_options(self) -> "ForecastCreate":
        if self.estimate_type not in settings.forecast_options.estimate_types:
            raise ValueError(f"unsupported estimate_type: {self.estimate_type}")
        if self.scenario not in settings.forecast_options.scenarios:
            raise ValueError(f"unsupported scenario: {self.scenario}")
        return self


class ForecastRead(SQLModel):
    id: int
    instrument_id: int
    scenario: str | None
    predicted_price: Decimal
    maturation_date: date
    prediction_date: date
    currency: str
    publisher_id: int
    conviction: int | None
    conviction_source: str | None
    horizon_source: str | None
    estimate_type: str | None
    method: str | None
    entry_mode: str | None


class ForecastOptionsRead(SQLModel):
    estimate_types: list[str]
    scenarios: list[str]
=======
    aggregate_components: list["AggregateComponent"] = Relationship(back_populates="forecast")
>>>>>>> 6ba6d72 (add forecast_aggregates and aggregate_components tables)
