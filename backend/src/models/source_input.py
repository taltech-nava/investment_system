from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .source import Source


class SourceInput(SQLModel, table=True):
    """Tracks which original sources a derived/processed source was built from."""

    __tablename__ = "source_inputs"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", index=True)
    input_source_id: int = Field(foreign_key="sources.id", index=True)

    source: Optional["Source"] = Relationship(
        back_populates="derived_inputs",
        sa_relationship_kwargs={
            "primaryjoin": "SourceInput.source_id == Source.id",
            "foreign_keys": "[SourceInput.source_id]",
        },
    )
    input_source: Optional["Source"] = Relationship(
        back_populates="original_inputs",
        sa_relationship_kwargs={
            "primaryjoin": "SourceInput.input_source_id == Source.id",
            "foreign_keys": "[SourceInput.input_source_id]",
        },
    )
