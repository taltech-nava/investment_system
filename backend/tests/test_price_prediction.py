"""Tests for the price prediction module: PricePredictionService and utilities."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from src.models.aggregate_component import AggregateComponent
from src.models.forecast import Forecast
from src.models.forecast_aggregate import ForecastAggregate
from src.models.instrument import Instrument
from src.models.publisher import Publisher
from src.services.price_prediction_service import (
    PricePredictionService,
    _conviction_from_cv,
    _decimal,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_forecast(
    session: Session,
    instrument_id: int,
    publisher_id: int,
    predicted_price: float,
    estimate_type: str = "source_point_estimate",
    scenario: str = "single",
    prediction_date: date | None = None,
    entry_mode: str | None = None,
) -> Forecast:
    price = Decimal(str(predicted_price))
    f = Forecast(
        instrument_id=instrument_id,
        publisher_id=publisher_id,
        prediction_date=prediction_date or date.today(),
        maturation_date=date.today() + timedelta(days=365),
        predicted_price=price,
        extracted_raw_price=price,  # NOT NULL on this branch; remove once nullable migration is merged
        currency="USD",
        estimate_type=estimate_type,
        scenario=scenario,
        entry_mode=entry_mode,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def aapl_id(db_session: Session) -> int:
    return db_session.exec(select(Instrument).where(Instrument.ticker == "AAPL")).first().id


@pytest.fixture()
def publisher(db_session: Session) -> Publisher:
    p = Publisher(institution="Test Bank")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


# ── Pure unit tests: _conviction_from_cv ─────────────────────────────────────


class TestConvictionFromCv:
    def test_cv_zero_returns_5(self) -> None:
        assert _conviction_from_cv(0.0) == 5

    def test_cv_below_0_03_returns_5(self) -> None:
        assert _conviction_from_cv(0.02) == 5

    def test_cv_exactly_0_03_returns_4(self) -> None:
        assert _conviction_from_cv(0.03) == 4  # not < 0.03

    def test_cv_between_0_03_and_0_07_returns_4(self) -> None:
        assert _conviction_from_cv(0.05) == 4

    def test_cv_exactly_0_07_returns_3(self) -> None:
        assert _conviction_from_cv(0.07) == 3

    def test_cv_between_0_07_and_0_12_returns_3(self) -> None:
        assert _conviction_from_cv(0.10) == 3

    def test_cv_exactly_0_12_returns_2(self) -> None:
        assert _conviction_from_cv(0.12) == 2

    def test_cv_between_0_12_and_0_20_returns_2(self) -> None:
        assert _conviction_from_cv(0.15) == 2

    def test_cv_exactly_0_20_returns_1(self) -> None:
        assert _conviction_from_cv(0.20) == 1

    def test_cv_above_0_20_returns_1(self) -> None:
        assert _conviction_from_cv(0.50) == 1
        assert _conviction_from_cv(1.0) == 1


# ── Pure unit tests: _decimal ─────────────────────────────────────────────────


class TestDecimal:
    def test_whole_number(self) -> None:
        assert _decimal(100.0) == Decimal("100.0000")

    def test_four_decimal_places(self) -> None:
        assert _decimal(1.23456789) == Decimal("1.2346")

    def test_round_half_up(self) -> None:
        assert _decimal(1.00005) == Decimal("1.0001")

    def test_negative(self) -> None:
        assert _decimal(-50.5) == Decimal("-50.5000")


# ── Pure unit tests: _conviction method ──────────────────────────────────────


class TestConvictionMethod:
    service = PricePredictionService()

    def test_single_price_returns_1(self) -> None:
        assert self.service._conviction([100.0]) == 1

    def test_zero_mean_returns_1(self) -> None:
        assert self.service._conviction([0.0, 0.0]) == 1

    def test_identical_prices_return_5(self) -> None:
        # stdev = 0 → cv = 0 → conviction 5
        assert self.service._conviction([100.0, 100.0, 100.0]) == 5

    def test_tight_cluster_high_conviction(self) -> None:
        # prices within ~1% of each other → cv ≈ 0.005 → conviction 5
        assert self.service._conviction([100.0, 100.5, 101.0, 100.3]) >= 4

    def test_wide_dispersion_low_conviction(self) -> None:
        # cv well above 0.20 → conviction 1
        assert self.service._conviction([50.0, 200.0, 350.0]) == 1

    def test_two_prices_identical_returns_5(self) -> None:
        assert self.service._conviction([100.0, 100.0]) == 5

    def test_two_prices_different_computes_cv(self) -> None:
        # stdev([80, 120]) = 20*sqrt(2)/sqrt(2)... actually stdev uses N-1
        # mean=100, stdev≈28.28, cv≈0.28 → conviction 1
        assert self.service._conviction([80.0, 120.0]) == 1


# ── Service integration tests: run() ─────────────────────────────────────────


class TestPricePredictionServiceRun:
    def test_no_forecasts_returns_no_data(self, db_session: Session, aapl_id: int) -> None:
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "no_data"
        assert result["count"] == 0

    def test_one_point_estimate_creates_averaged_point_aggregate(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "ok"
        types = {(a["estimate_type"], a["scenario"]) for a in result["aggregates"]}
        assert ("averaged_point_estimate", "single") in types

    def test_fewer_than_3_point_estimates_no_source_scenario(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        make_forecast(db_session, aapl_id, publisher.id, 120.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert not any(
            a["estimate_type"] == "source_scenario_estimate" for a in result["aggregates"]
        )

    def test_three_point_estimates_creates_source_scenario_bear_base_bull(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [80.0, 100.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        types = {(a["estimate_type"], a["scenario"]) for a in result["aggregates"]}
        assert ("source_scenario_estimate", "bear") in types
        assert ("source_scenario_estimate", "base") in types
        assert ("source_scenario_estimate", "bull") in types

    def test_point_estimate_average_correct(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        make_forecast(db_session, aapl_id, publisher.id, 200.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        agg = next(
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_point_estimate"
        )
        assert agg["predicted_price"] == pytest.approx(150.0)

    def test_llm_point_estimate_included_in_averaged_point(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0, estimate_type="llm_point_estimate")
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "ok"
        assert any(a["estimate_type"] == "averaged_point_estimate" for a in result["aggregates"])

    def test_llm_scenario_estimates_averaged_per_scenario(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            70.0,
            estimate_type="llm_scenario_estimate",
            scenario="bear",
        )
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            90.0,
            estimate_type="llm_scenario_estimate",
            scenario="bear",
        )
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            110.0,
            estimate_type="llm_scenario_estimate",
            scenario="base",
        )
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {(a["estimate_type"], a["scenario"]): a for a in result["aggregates"]}
        assert ("averaged_scenario_estimate", "bear") in aggs
        assert aggs[("averaged_scenario_estimate", "bear")]["predicted_price"] == pytest.approx(
            80.0
        )
        assert ("averaged_scenario_estimate", "base") in aggs
        assert ("averaged_scenario_estimate", "bull") not in aggs

    def test_only_bear_scenario_creates_only_bear_aggregate(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            70.0,
            estimate_type="llm_scenario_estimate",
            scenario="bear",
        )
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        scenario_aggs = [
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_scenario_estimate"
        ]
        assert len(scenario_aggs) == 1
        assert scenario_aggs[0]["scenario"] == "bear"

    def test_forecasts_older_than_365_days_excluded(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        old_date = date.today() - timedelta(days=366)
        make_forecast(db_session, aapl_id, publisher.id, 100.0, prediction_date=old_date)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "no_data"

    def test_forecast_exactly_365_days_old_included(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        cutoff_date = date.today() - timedelta(days=365)
        make_forecast(db_session, aapl_id, publisher.id, 100.0, prediction_date=cutoff_date)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "ok"

    def test_manual_point_estimate_excluded(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            100.0,
            estimate_type="manual_point_estimate",
            entry_mode="manual",
        )
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "no_data"

    def test_manual_scenario_estimate_excluded(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            100.0,
            estimate_type="manual_scenario_estimate",
            scenario="bull",
            entry_mode="manual",
        )
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["status"] == "no_data"

    def test_manual_entries_do_not_contaminate_external_aggregate(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session,
            aapl_id,
            publisher.id,
            200.0,
            estimate_type="manual_point_estimate",
            entry_mode="manual",
        )
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        agg = next(
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_point_estimate"
        )
        assert agg["predicted_price"] == pytest.approx(100.0)
        assert agg["source_count"] == 1

    def test_source_count_reflects_included_forecasts_only(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        make_forecast(db_session, aapl_id, publisher.id, 110.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["source_count"] == 2

    def test_conviction_source_is_calculated(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        PricePredictionService().run(db_session, aapl_id, "USD")
        agg = db_session.exec(
            select(ForecastAggregate).where(ForecastAggregate.instrument_id == aapl_id)
        ).first()
        assert agg.conviction_source == "calculated"

    def test_maturation_date_is_today_plus_365(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        PricePredictionService().run(db_session, aapl_id, "USD")
        agg = db_session.exec(
            select(ForecastAggregate).where(ForecastAggregate.instrument_id == aapl_id)
        ).first()
        assert agg.maturation_date == date.today() + timedelta(days=365)

    def test_prediction_date_is_today(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        PricePredictionService().run(db_session, aapl_id, "USD")
        agg = db_session.exec(
            select(ForecastAggregate).where(ForecastAggregate.instrument_id == aapl_id)
        ).first()
        assert agg.prediction_date == date.today()

    def test_aggregate_components_link_correct_forecasts(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f1 = make_forecast(db_session, aapl_id, publisher.id, 100.0)
        f2 = make_forecast(db_session, aapl_id, publisher.id, 110.0)
        PricePredictionService().run(db_session, aapl_id, "USD")
        agg = db_session.exec(
            select(ForecastAggregate).where(
                ForecastAggregate.estimate_type == "averaged_point_estimate"
            )
        ).first()
        components = db_session.exec(
            select(AggregateComponent).where(AggregateComponent.aggregate_id == agg.id)
        ).all()
        linked_ids = {c.forecast_id for c in components}
        assert f1.id in linked_ids
        assert f2.id in linked_ids

    def test_conviction_1_for_single_price(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, 100.0)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        agg = next(
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_point_estimate"
        )
        assert agg["conviction"] == 1

    def test_conviction_high_for_tight_cluster(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [100.0, 100.5, 101.0, 100.2, 100.8]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        agg = next(
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_point_estimate"
        )
        assert agg["conviction"] >= 4

    def test_conviction_1_for_wide_dispersion(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [50.0, 150.0, 300.0, 500.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        agg = next(
            a for a in result["aggregates"] if a["estimate_type"] == "averaged_point_estimate"
        )
        assert agg["conviction"] == 1

    def test_aggregates_created_count_correct(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # 3 point estimates → averaged_point_estimate + 3 source_scenario_estimate = 4
        for price in [80.0, 100.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        assert result["aggregates_created"] == 4


# ── Tercile splitting tests ───────────────────────────────────────────────────


class TestTercileSplitting:
    def test_three_forecasts_one_per_group(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [80.0, 100.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {
            a["scenario"]: a
            for a in result["aggregates"]
            if a["estimate_type"] == "source_scenario_estimate"
        }
        assert aggs["bear"]["predicted_price"] == pytest.approx(80.0)
        assert aggs["base"]["predicted_price"] == pytest.approx(100.0)
        assert aggs["bull"]["predicted_price"] == pytest.approx(120.0)

    def test_six_forecasts_split_evenly(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [60.0, 70.0, 80.0, 90.0, 100.0, 110.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {
            a["scenario"]: a
            for a in result["aggregates"]
            if a["estimate_type"] == "source_scenario_estimate"
        }
        assert aggs["bear"]["predicted_price"] == pytest.approx(65.0)  # mean(60, 70)
        assert aggs["base"]["predicted_price"] == pytest.approx(85.0)  # mean(80, 90)
        assert aggs["bull"]["predicted_price"] == pytest.approx(105.0)  # mean(100, 110)

    def test_four_forecasts_remainder_goes_to_bull(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # n=4, third=1: bear=[60], base=[70], bull=[80, 90]
        for price in [60.0, 70.0, 80.0, 90.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {
            a["scenario"]: a
            for a in result["aggregates"]
            if a["estimate_type"] == "source_scenario_estimate"
        }
        assert aggs["bear"]["predicted_price"] == pytest.approx(60.0)
        assert aggs["base"]["predicted_price"] == pytest.approx(70.0)
        assert aggs["bull"]["predicted_price"] == pytest.approx(85.0)  # mean(80, 90)
        assert aggs["bull"]["source_count"] == 2

    def test_seven_forecasts_remainder_goes_to_bull(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # n=7, third=2: bear=[10,20], base=[30,40], bull=[50,60,70]
        for price in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {
            a["scenario"]: a
            for a in result["aggregates"]
            if a["estimate_type"] == "source_scenario_estimate"
        }
        assert aggs["bear"]["source_count"] == 2
        assert aggs["base"]["source_count"] == 2
        assert aggs["bull"]["source_count"] == 3

    def test_bear_always_lowest_prices(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [200.0, 50.0, 100.0, 150.0, 75.0, 175.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        result = PricePredictionService().run(db_session, aapl_id, "USD")
        aggs = {
            a["scenario"]: a
            for a in result["aggregates"]
            if a["estimate_type"] == "source_scenario_estimate"
        }
        assert (
            aggs["bear"]["predicted_price"]
            < aggs["base"]["predicted_price"]
            < aggs["bull"]["predicted_price"]
        )


# ── API endpoint tests ────────────────────────────────────────────────────────


class TestPredictEndpoint:
    def test_ticker_not_found_returns_404(self, client: object) -> None:
        response = client.post("/forecasts/predict/NOTEXIST")
        assert response.status_code == 404

    def test_no_source_forecasts_returns_422(self, client: object) -> None:
        response = client.post("/forecasts/predict/AAPL")
        assert response.status_code == 422
        assert "No source forecasts" in response.json()["detail"]

    def test_success_returns_200(
        self, client: object, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [100.0, 110.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        assert client.post("/forecasts/predict/AAPL").status_code == 200

    def test_success_response_structure(
        self, client: object, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [100.0, 110.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        data = client.post("/forecasts/predict/AAPL").json()
        assert data["status"] == "ok"
        assert data["source_count"] == 3
        assert data["aggregates_created"] > 0
        assert isinstance(data["aggregates"], list)

    def test_success_aggregate_has_required_fields(
        self, client: object, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        for price in [100.0, 110.0, 120.0]:
            make_forecast(db_session, aapl_id, publisher.id, price)
        agg = client.post("/forecasts/predict/AAPL").json()["aggregates"][0]
        for field in (
            "id",
            "estimate_type",
            "scenario",
            "predicted_price",
            "conviction",
            "source_count",
        ):
            assert field in agg
