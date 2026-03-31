from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .instrument import Instrument


class Price(SQLModel, table=True):
    __tablename__ = "prices"

    id: int | None = Field(default=None, primary_key=True)
    instrument_id: int = Field(foreign_key="instruments.id", index=True)
    price_date: date = Field(index=True)
    price: Decimal = Field(sa_column=Column(Numeric(12, 4), nullable=False))
    currency: str = Field(max_length=10)
    data_source: str | None = Field(default=None, max_length=100)

    instrument: Optional["Instrument"] = Relationship(back_populates="prices")
