"""create investment schema tables

Revision ID: b2c3d4e5f6a1
Revises:
Create Date: 2026-03-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a1"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instrument_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "publishers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("authors", sa.JSON(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("quality_rank", sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["instrument_classes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("publisher_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("search_subjects", sa.JSON(), nullable=True),
        sa.Column("search_intents", sa.JSON(), nullable=True),
        sa.Column("search_filetypes", sa.JSON(), nullable=True),
        sa.Column("search_title_block", sa.JSON(), nullable=True),
        sa.Column("search_org_block", sa.JSON(), nullable=True),
        sa.Column("search_date_after", sa.Date(), nullable=True),
        sa.Column("search_date_before", sa.Date(), nullable=True),
        sa.Column("search_engine", sa.String(length=50), nullable=True),
        sa.Column("search_query_full", sa.Text(), nullable=True),
        sa.Column("horizon_context", sa.String(length=50), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=True),
        sa.Column("fetch_date", sa.Date(), nullable=True),
        sa.Column("audit_status", sa.String(length=10), nullable=True),
        sa.Column("rejection_reason", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["publisher_id"], ["publishers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("publisher_id", sa.Integer(), nullable=False),
        sa.Column("prediction_date", sa.Date(), nullable=False),
        sa.Column("maturation_date", sa.Date(), nullable=False),
        sa.Column("horizon_source", sa.String(length=10), nullable=True),
        sa.Column("extracted_raw_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("extracted_raw_price_run", sa.SmallInteger(), nullable=True),
        sa.Column("extraction_status", sa.String(length=25), nullable=True),
        sa.Column("predicted_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("conviction", sa.SmallInteger(), nullable=True),
        sa.Column("conviction_source", sa.String(length=10), nullable=True),
        sa.Column("method", sa.String(length=100), nullable=True),
        sa.Column("entry_mode", sa.String(length=20), nullable=True),
        sa.Column("estimate_type", sa.String(length=25), nullable=True),
        sa.Column("scenario", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["publisher_id"], ["publishers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "forecast_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "source_inputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("input_source_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["input_source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(12, 4), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("data_source", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("actual_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("price_return_error", sa.Numeric(8, 4), nullable=False),
        sa.Column("direction_correct", sa.Boolean(), nullable=True),
        sa.Column("divergence_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Instruments ---
    op.create_index("ix_instruments_class_id", "instruments", ["class_id"])
    op.create_index("ix_instruments_ticker", "instruments", ["ticker"], unique=True)
    op.create_index("ix_instruments_name", "instruments", ["name"])

    # --- Forecasts ---
    op.create_index("ix_forecasts_instrument_id", "forecasts", ["instrument_id"])
    op.create_index("ix_forecasts_publisher_id", "forecasts", ["publisher_id"])
    op.create_index("ix_forecasts_prediction_date", "forecasts", ["prediction_date"])
    op.create_index("ix_forecasts_maturation_date", "forecasts", ["maturation_date"])
    op.create_index(
        "ix_forecasts_instrument_maturation", "forecasts", ["instrument_id", "maturation_date"]
    )

    # --- Sources ---
    op.create_index("ix_sources_publisher_id", "sources", ["publisher_id"])
    op.create_index("ix_sources_file_path", "sources", ["file_path"])
    op.create_index("ix_sources_audit_status", "sources", ["audit_status"])
    op.create_index("ix_sources_fetch_date", "sources", ["fetch_date"])
    op.create_index("ix_sources_search_engine", "sources", ["search_engine"])
    op.create_index(
        "ix_sources_search_query_full", "sources", ["search_query_full"], postgresql_using="hash"
    )

    # --- Forecast sources (junction) ---
    op.create_index("ix_forecast_sources_forecast_id", "forecast_sources", ["forecast_id"])
    op.create_index("ix_forecast_sources_source_id", "forecast_sources", ["source_id"])

    # --- Source inputs ---
    op.create_index("ix_source_inputs_source_id", "source_inputs", ["source_id"])
    op.create_index("ix_source_inputs_input_source_id", "source_inputs", ["input_source_id"])

    # --- Prices ---
    op.create_index("ix_prices_instrument_id", "prices", ["instrument_id"])
    op.create_index("ix_prices_price_date", "prices", ["price_date"])

    # --- Reports ---
    op.create_index("ix_reports_forecast_id", "reports", ["forecast_id"])
    op.create_index("ix_reports_review_date", "reports", ["review_date"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("prices")
    op.drop_table("source_inputs")
    op.drop_table("forecast_sources")
    op.drop_table("forecasts")
    op.drop_table("sources")
    op.drop_table("instruments")
    op.drop_table("publishers")
    op.drop_table("instrument_classes")
