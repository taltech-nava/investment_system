from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric, SmallInteger
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .aggregate_component import AggregateComponent
    from .instrument import Instrument


class ForecastAggregate(SQLModel, table=True):
    __tablename__ = "forecast_aggregates"

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instruments.id", index=True)

    estimate_type: str = Field(max_length=25)
    # averaged_point_estimate: unweighted arithmetic mean of source_point_estimate forecasts
    # averaged_scenario_estimate: unweighted arithmetic mean of llm_scenario_estimate forecasts per scenario
    # source_scenario_estimate: derived bear/base/bull grouping of source_point_estimate forecasts

    scenario: str = Field(max_length=10)
    # single: for averaged_point_estimate
    # bear, base, bull: for scenario-based aggregates

    predicted_price: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    currency: str = Field(max_length=10)

    prediction_date: date = Field(index=True)
    maturation_date: date = Field(index=True)
    calculated_at: datetime = Field(index=True)

    conviction: int | None = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    conviction_source: str | None = Field(default=None, max_length=10)
    # conviction_source is always 'calculated' — kept for future manual override capability

    source_count: int = Field(sa_column=Column(SmallInteger, nullable=False))

    instrument: Optional["Instrument"] = Relationship(back_populates="forecast_aggregates")
    components: list["AggregateComponent"] = Relationship(back_populates="aggregate")
