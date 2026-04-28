from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .forecast_source import ForecastSource
    from .publisher import Publisher
    from .source_input import SourceInput


class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: int | None = Field(default=None, primary_key=True)
    publisher_id: int | None = Field(default=None, foreign_key="publishers.id", index=True)
    title: str | None = Field(default=None)
    file_path: str | None = Field(default=None, index=True)
    snippet_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    search_subjects: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    search_intents: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    search_filetypes: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    search_title_block: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    search_org_block: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    search_date_after: date | None = Field(default=None)
    search_date_before: date | None = Field(default=None)
    search_engine: str | None = Field(default=None, max_length=50, index=True)
    search_query_full: str | None = Field(default=None)
    horizon_context: str | None = Field(default=None, max_length=50)
    mode: str | None = Field(default=None, max_length=20)
    fetch_date: date | None = Field(default=None, index=True)

    audit_status: str | None = Field(default=None, max_length=10, index=True)
    rejection_reason: str | None = Field(default=None, max_length=20)

    publisher: Optional["Publisher"] = Relationship(back_populates="sources")
    forecast_sources: list["ForecastSource"] = Relationship(back_populates="source")

    derived_inputs: list["SourceInput"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={
            "primaryjoin": "SourceInput.source_id == Source.id",
            "foreign_keys": "[SourceInput.source_id]",
        },
    )

    original_inputs: list["SourceInput"] = Relationship(
        back_populates="input_source",
        sa_relationship_kwargs={
            "primaryjoin": "SourceInput.input_source_id == Source.id",
            "foreign_keys": "[SourceInput.input_source_id]",
        },
    )
