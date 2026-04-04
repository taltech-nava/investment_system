from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .instrument import Instrument


class InstrumentClass(SQLModel, table=True):
    __tablename__ = "instrument_classes"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)

    instruments: list["Instrument"] = Relationship(back_populates="instrument_class")
