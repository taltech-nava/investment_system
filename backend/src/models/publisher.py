from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, SmallInteger
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast import Forecast
    from .source import Source


class Publisher(SQLModel, table=True):
    __tablename__ = "publishers"

    id: int | None = Field(default=None, primary_key=True)
    institution: str | None = Field(default=None, max_length=255)
    authors: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    title: str | None = Field(default=None)
    publication_date: date | None = Field(default=None)
    url: str | None = Field(default=None)
    method: str | None = Field(default=None, max_length=50)
    quality_rank: int | None = Field(default=None, sa_column=Column(SmallInteger, nullable=True))

    forecasts: list["Forecast"] = Relationship(back_populates="publisher")
    sources: list["Source"] = Relationship(back_populates="publisher")
