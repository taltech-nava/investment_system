from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import mean, stdev
from typing import TYPE_CHECKING

from src.models.forecast_aggregate import ForecastAggregate
from src.repositories.forecast_aggregate_repository import forecast_aggregate_repository

if TYPE_CHECKING:
    from sqlmodel import Session

    from src.models.forecast import Forecast

# Only forecasts with prediction_date within this window are used.
LOOKBACK_DAYS = 365


def _conviction_from_cv(cv: float) -> int:
    """
    Maps coefficient of variation (std / mean) to a 1-5 conviction score.
    Lower dispersion → higher conviction.

    CV thresholds (empirically reasonable for analyst price targets):
      < 0.03  → 5  (very tight cluster)
      < 0.07  → 4
      < 0.12  → 3
      < 0.20  → 2
      >= 0.20 → 1  (wide dispersion)
    """
    if cv < 0.03:
        return 5
    if cv < 0.07:
        return 4
    if cv < 0.12:
        return 3
    if cv < 0.20:
        return 2
    return 1


def _decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


class PricePredictionService:
    def run(self, session: Session, instrument_id: int, currency: str) -> dict:
        """
        Reads recent source forecasts for the instrument, computes aggregates,
        and persists them to forecast_aggregates + aggregate_components.

        Returns a summary dict with the results and metadata.
        """
        since = date.today() - timedelta(days=LOOKBACK_DAYS)
        forecasts = forecast_aggregate_repository.get_source_forecasts(
            session, instrument_id, since
        )

        if not forecasts:
            return {"status": "no_data", "instrument_id": instrument_id, "count": 0}

        results = []

        # --- Point estimate ---
        point_forecasts = [
            f for f in forecasts
            if f.estimate_type in ("source_point_estimate", "llm_point_estimate")
        ]
        if point_forecasts:
            results.append(
                self._build_aggregate(
                    session=session,
                    instrument_id=instrument_id,
                    currency=currency,
                    estimate_type="averaged_point_estimate",
                    scenario="single",
                    forecasts=point_forecasts,
                )
            )

        # --- Scenario estimates from llm_scenario_estimate rows ---
        scenario_forecasts = [f for f in forecasts if f.estimate_type == "llm_scenario_estimate"]
        for scenario_label in ("bear", "base", "bull"):
            group = [f for f in scenario_forecasts if f.scenario == scenario_label]
            if group:
                results.append(
                    self._build_aggregate(
                        session=session,
                        instrument_id=instrument_id,
                        currency=currency,
                        estimate_type="averaged_scenario_estimate",
                        scenario=scenario_label,
                        forecasts=group,
                    )
                )

        # --- Source scenario estimate: bear/base/bull derived from point forecasts ---
        if len(point_forecasts) >= 3:
            results.extend(
                self._build_source_scenario_aggregates(
                    session=session,
                    instrument_id=instrument_id,
                    currency=currency,
                    forecasts=point_forecasts,
                )
            )

        return {
            "status": "ok",
            "instrument_id": instrument_id,
            "source_count": len(forecasts),
            "aggregates_created": len(results),
            "aggregates": results,
        }

    def _build_aggregate(
        self,
        session: Session,
        instrument_id: int,
        currency: str,
        estimate_type: str,
        scenario: str,
        forecasts: list[Forecast],
    ) -> dict:
        prices = [float(f.predicted_price) for f in forecasts]
        avg = mean(prices)
        conviction = self._conviction(prices)
        today = date.today()

        aggregate = ForecastAggregate(
            instrument_id=instrument_id,
            estimate_type=estimate_type,
            scenario=scenario,
            predicted_price=_decimal(avg),
            currency=currency,
            prediction_date=today,
            maturation_date=today + timedelta(days=365),
            calculated_at=datetime.now(tz=UTC),
            conviction=conviction,
            conviction_source="calculated",
            source_count=len(forecasts),
        )

        saved = forecast_aggregate_repository.save_aggregate(
            session=session,
            aggregate=aggregate,
            component_forecast_ids=[f.id for f in forecasts],
        )

        return {
            "id": saved.id,
            "estimate_type": estimate_type,
            "scenario": scenario,
            "predicted_price": float(saved.predicted_price),
            "conviction": conviction,
            "source_count": len(forecasts),
        }

    def _build_source_scenario_aggregates(
        self,
        session: Session,
        instrument_id: int,
        currency: str,
        forecasts: list[Forecast],
    ) -> list[dict]:
        """
        Splits point forecasts into three equal groups by predicted_price,
        computes the mean of each group, and stores as source_scenario_estimate.
        """
        sorted_forecasts = sorted(forecasts, key=lambda f: float(f.predicted_price))
        n = len(sorted_forecasts)
        third = n // 3

        groups = {
            "bear": sorted_forecasts[:third],
            "base": sorted_forecasts[third: third * 2],
            "bull": sorted_forecasts[third * 2:],
        }

        results = []
        for scenario_label, group in groups.items():
            if group:
                results.append(
                    self._build_aggregate(
                        session=session,
                        instrument_id=instrument_id,
                        currency=currency,
                        estimate_type="source_scenario_estimate",
                        scenario=scenario_label,
                        forecasts=group,
                    )
                )
        return results

    def _conviction(self, prices: list[float]) -> int:
        if len(prices) < 2:
            return 1
        avg = mean(prices)
        if avg == 0:
            return 1
        cv = stdev(prices) / avg
        return _conviction_from_cv(cv)


price_prediction_service = PricePredictionService()
