"""make_extracted_raw_price_nullable

Revision ID: a143eddba07b
Revises: c3d4e5f6a1b2
Create Date: 2026-04-22 11:10:57.829981

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a143eddba07b"
down_revision: str | Sequence[str] | None = "c3d4e5f6a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "forecasts", "extracted_raw_price", existing_type=sa.Numeric(12, 4), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "forecasts", "extracted_raw_price", existing_type=sa.Numeric(12, 4), nullable=False
    )
