"""add spot_price_at_prediction to forecasts

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-02

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "forecasts",
        sa.Column("spot_price_at_prediction", sa.Numeric(12, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("forecasts", "spot_price_at_prediction")
