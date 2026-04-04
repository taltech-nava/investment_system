from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast import Forecast


class Report(SQLModel, table=True):
    """Accuracy review of a forecast once its maturation date has passed."""

    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    forecast_id: int = Field(foreign_key="forecasts.id", index=True)
    review_date: date = Field(index=True)
    actual_price: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    price_return_error: Decimal = Field(sa_column=Column(Numeric(8, 4), nullable=False))
    direction_correct: bool | None = Field(default=None)
    divergence_notes: str | None = Field(default=None)

    forecast: Optional["Forecast"] = Relationship(back_populates="reports")
