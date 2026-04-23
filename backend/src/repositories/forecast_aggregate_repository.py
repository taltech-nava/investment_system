from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from src.models.aggregate_component import AggregateComponent
from src.models.forecast import Forecast

if TYPE_CHECKING:
    from datetime import date

    from src.models.forecast_aggregate import ForecastAggregate


class ForecastAggregateRepository:
    def get_source_forecasts(
        self,
        session: Session,
        instrument_id: int,
        since: date,
    ) -> list[Forecast]:
        """
        Returns all source_point_estimate and llm_scenario_estimate forecasts
        for an instrument with prediction_date >= since.
        """
        return list(
            session.exec(
                select(Forecast).where(
                    Forecast.instrument_id == instrument_id,
                    Forecast.estimate_type.in_(
                        ["source_point_estimate", "llm_point_estimate", "llm_scenario_estimate"]
                    ),
                    Forecast.prediction_date >= since,
                    Forecast.predicted_price.isnot(None),
                )
            ).all()
        )

    def save_aggregate(
        self,
        session: Session,
        aggregate: ForecastAggregate,
        component_forecast_ids: list[int],
    ) -> ForecastAggregate:
        """
        Persists a ForecastAggregate and its AggregateComponent provenance rows
        in a single transaction.
        """
        session.add(aggregate)
        session.flush()  # get aggregate.id before inserting components

        for forecast_id in component_forecast_ids:
            session.add(
                AggregateComponent(
                    aggregate_id=aggregate.id,
                    forecast_id=forecast_id,
                )
            )

        session.commit()
        session.refresh(aggregate)
        return aggregate


forecast_aggregate_repository = ForecastAggregateRepository()
