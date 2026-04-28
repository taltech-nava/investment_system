"""make predicted_price nullable

Revision ID: d1e2f3a4b5c6
Revises: ba2e85796875
Create Date: 2026-04-23

Reason: LLM-extracted rows may exist in an unverified state awaiting human
review. predicted_price cannot be set until the human confirms the value.
Rows with predicted_price IS NULL are excluded from forecast_aggregates by
the aggregate repository filter. See docs/schema_decisions.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "ba2e85796875"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("forecasts") as batch_op:
        batch_op.alter_column(
            "predicted_price",
            existing_type=sa.Numeric(12, 4),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("forecasts") as batch_op:
        batch_op.alter_column(
            "predicted_price",
            existing_type=sa.Numeric(12, 4),
            nullable=False,
        )
