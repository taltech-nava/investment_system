"""add forecast_aggregates and aggregate_components

Revision ID: ba2e85796875
Revises: 398163f7cb65
Create Date: 2026-04-08 13:42:05.010958

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ba2e85796875'
down_revision: str | Sequence[str] | None = 'd49c6f591ba3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "forecast_aggregates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("estimate_type", sa.String(length=25), nullable=False),
        sa.Column("scenario", sa.String(length=10), nullable=False),
        sa.Column("predicted_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("prediction_date", sa.Date(), nullable=False),
        sa.Column("maturation_date", sa.Date(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.Column("conviction", sa.SmallInteger(), nullable=True),
        sa.Column("conviction_source", sa.String(length=10), nullable=True),
        sa.Column("source_count", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecast_aggregates_instrument_id", "forecast_aggregates", ["instrument_id"])
    op.create_index("ix_forecast_aggregates_prediction_date", "forecast_aggregates", ["prediction_date"])
    op.create_index("ix_forecast_aggregates_maturation_date", "forecast_aggregates", ["maturation_date"])
    op.create_index("ix_forecast_aggregates_calculated_at", "forecast_aggregates", ["calculated_at"])

    op.create_table(
        "aggregate_components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aggregate_id", sa.Integer(), nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["aggregate_id"], ["forecast_aggregates.id"]),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aggregate_components_aggregate_id", "aggregate_components", ["aggregate_id"])
    op.create_index("ix_aggregate_components_forecast_id", "aggregate_components", ["forecast_id"])

    op.create_check_constraint(
        "chk_forecast_estimate_type",
        "forecasts",
        "estimate_type IN ('source_point_estimate', 'llm_point_estimate', 'llm_scenario_estimate', 'manual_point_estimate', 'manual_scenario_estimate')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("chk_forecast_estimate_type", "forecasts", type_="check")
    op.drop_index("ix_aggregate_components_forecast_id", table_name="aggregate_components")
    op.drop_index("ix_aggregate_components_aggregate_id", table_name="aggregate_components")
    op.drop_table("aggregate_components")
    op.drop_index("ix_forecast_aggregates_calculated_at", table_name="forecast_aggregates")
    op.drop_index("ix_forecast_aggregates_maturation_date", table_name="forecast_aggregates")
    op.drop_index("ix_forecast_aggregates_prediction_date", table_name="forecast_aggregates")
    op.drop_index("ix_forecast_aggregates_instrument_id", table_name="forecast_aggregates")
    op.drop_table("forecast_aggregates")
