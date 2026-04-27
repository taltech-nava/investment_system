"""make_extracted_raw_price_nullable

Revision ID: d49c6f591ba3
Revises: c3d4e5f6a1b2
Create Date: 2026-04-20 20:53:41.011205

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d49c6f591ba3"
down_revision: str | None = "1c5a0442d917"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "forecasts",
        "extracted_raw_price",
        existing_type=sa.Numeric(12, 4),
        nullable=True,
    )
    op.alter_column(
        "forecasts",
        "horizon_source",
        existing_type=sa.String(length=10),
        type_=sa.String(length=30),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "forecasts",
        "horizon_source",
        existing_type=sa.String(length=30),
        type_=sa.String(length=10),
        existing_nullable=True,
    )
    op.alter_column(
        "forecasts",
        "extracted_raw_price",
        existing_type=sa.Numeric(12, 4),
        nullable=False,
    )
