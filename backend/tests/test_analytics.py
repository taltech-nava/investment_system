"""Tests for the analytics module: _bin, AnalyticsService, and the distribution endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.forecast import Forecast
from src.models.instrument import Instrument
from src.models.publisher import Publisher
from src.models.report import Report
from src.services.analytics_service import AnalyticsService, _bin

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_publisher(session: Session, institution: str = "Test Bank") -> Publisher:
    p = Publisher(institution=institution)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def make_forecast(
    session: Session,
    instrument_id: int,
    publisher_id: int,
    predicted_price: float = 100.0,
) -> Forecast:
    price = Decimal(str(predicted_price))
    f = Forecast(
        instrument_id=instrument_id,
        publisher_id=publisher_id,
        prediction_date=date.today(),
        maturation_date=date(2026, 1, 1),
        predicted_price=price,
        extracted_raw_price=price,
        currency="USD",
        estimate_type="source_point_estimate",
        scenario="single",
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


def make_report(
    session: Session,
    forecast_id: int,
    price_return_error: float,
) -> Report:
    r = Report(
        forecast_id=forecast_id,
        review_date=date.today(),
        actual_price=Decimal("100.00"),
        price_return_error=Decimal(str(price_return_error)),
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def aapl_id(db_session: Session) -> int:
    return (
        db_session.exec(
            __import__("sqlmodel", fromlist=["select"])
            .select(Instrument)
            .where(Instrument.ticker == "AAPL")
        )
        .first()
        .id
    )


@pytest.fixture()
def abnb_id(db_session: Session) -> int:
    return (
        db_session.exec(
            __import__("sqlmodel", fromlist=["select"])
            .select(Instrument)
            .where(Instrument.ticker == "ABNB")
        )
        .first()
        .id
    )


@pytest.fixture()
def publisher(db_session: Session) -> Publisher:
    return make_publisher(db_session)


# ── Unit tests: _bin ──────────────────────────────────────────────────────────


class TestBin:
    def test_empty_list_returns_all_zeros(self) -> None:
        assert _bin([]) == [0] * 20

    def test_value_below_first_cutoff_lands_in_bucket_0(self) -> None:
        assert _bin([-0.95])[0] == 1
        assert sum(_bin([-0.95])) == 1

    def test_value_exactly_minus_090_lands_in_bucket_1(self) -> None:
        assert _bin([-0.90])[1] == 1

    def test_value_exactly_0_lands_in_bucket_10(self) -> None:
        assert _bin([0.00])[10] == 1

    def test_value_above_100_clamped_to_last_bucket(self) -> None:
        assert _bin([1.50])[19] == 1
        assert sum(_bin([1.50])) == 1

    def test_value_exactly_100_clamped_to_last_bucket(self) -> None:
        assert _bin([1.00])[19] == 1

    def test_counts_sum_to_input_length(self) -> None:
        errors = [-0.95, -0.50, -0.20, 0.00, 0.20, 0.50, 0.95]
        assert sum(_bin(errors)) == len(errors)

    def test_each_value_lands_in_distinct_bucket(self) -> None:
        errors = [-0.95, -0.50, -0.20, 0.00, 0.20, 0.50, 0.95]
        counts = _bin(errors)
        assert all(c <= 1 for c in counts)


# ── Service integration tests ─────────────────────────────────────────────────


class TestAnalyticsServiceNoFilter:
    def test_no_reports_returns_zero_bins(self, db_session: Session) -> None:
        result = AnalyticsService().get_distribution(db_session)
        assert result.all == [0] * 20
        assert result.selected == [0] * 20

    def test_no_reports_returns_null_means(self, db_session: Session) -> None:
        result = AnalyticsService().get_distribution(db_session)
        assert result.mean_all is None
        assert result.mean_selected is None

    def test_no_reports_not_significant(self, db_session: Session) -> None:
        result = AnalyticsService().get_distribution(db_session)
        assert result.significant is False
        assert result.p_value is None

    def test_no_filter_selected_equals_all(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        result = AnalyticsService().get_distribution(db_session)
        assert result.all == result.selected
        assert result.mean_all == result.mean_selected

    def test_bins_field_is_correct_labels(self, db_session: Session) -> None:
        result = AnalyticsService().get_distribution(db_session)
        assert result.bins == [
            -1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, -0.20, -0.10,
             0.00,  0.10,  0.20,  0.30,  0.40,  0.50,  0.60,  0.70,  0.80,  0.90,  1.00,
        ]

    def test_mean_all_computed_correctly(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f1 = make_forecast(db_session, aapl_id, publisher.id)
        f2 = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f1.id, 0.10)
        make_report(db_session, f2.id, -0.10)
        result = AnalyticsService().get_distribution(db_session)
        assert result.mean_all == pytest.approx(0.0, abs=1e-4)

    def test_no_filter_no_p_value(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        result = AnalyticsService().get_distribution(db_session)
        assert result.p_value is None
        assert result.significant is False


class TestAnalyticsServiceTickerFilter:
    def test_ticker_filter_returns_only_matching_errors(
        self,
        db_session: Session,
        aapl_id: int,
        abnb_id: int,
        publisher: Publisher,
    ) -> None:
        fa = make_forecast(db_session, aapl_id, publisher.id)
        fb = make_forecast(db_session, abnb_id, publisher.id)
        make_report(db_session, fa.id, 0.05)
        make_report(db_session, fb.id, -0.20)
        result = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        # selected contains only AAPL error (0.05 → bucket 10)
        assert result.selected[10] == 1
        assert sum(result.selected) == 1

    def test_ticker_filter_all_contains_both_instruments(
        self,
        db_session: Session,
        aapl_id: int,
        abnb_id: int,
        publisher: Publisher,
    ) -> None:
        fa = make_forecast(db_session, aapl_id, publisher.id)
        fb = make_forecast(db_session, abnb_id, publisher.id)
        make_report(db_session, fa.id, 0.05)
        make_report(db_session, fb.id, -0.20)
        result = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        assert sum(result.all) == 2

    def test_ticker_case_insensitive(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        r_lower = AnalyticsService().get_distribution(db_session, ticker="aapl")
        r_upper = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        assert r_lower.selected == r_upper.selected

    def test_unknown_ticker_returns_empty_selected(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        result = AnalyticsService().get_distribution(db_session, ticker="ZZZZ")
        assert result.selected == [0] * 20
        assert result.mean_selected is None

    def test_p_value_computed_with_sufficient_data(
        self,
        db_session: Session,
        aapl_id: int,
        abnb_id: int,
        publisher: Publisher,
    ) -> None:
        for error in [0.05, -0.03, 0.12, -0.08, 0.02]:
            f = make_forecast(db_session, aapl_id, publisher.id)
            make_report(db_session, f.id, error)
        for error in [0.30, 0.25, 0.28, 0.35, 0.22]:
            f = make_forecast(db_session, abnb_id, publisher.id)
            make_report(db_session, f.id, error)
        result = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        assert result.p_value is not None
        assert 0.0 <= result.p_value <= 1.0

    def test_significant_flag_matches_p_value(
        self,
        db_session: Session,
        aapl_id: int,
        abnb_id: int,
        publisher: Publisher,
    ) -> None:
        for error in [0.05, -0.03, 0.12, -0.08, 0.02]:
            f = make_forecast(db_session, aapl_id, publisher.id)
            make_report(db_session, f.id, error)
        for error in [0.30, 0.25, 0.28, 0.35, 0.22]:
            f = make_forecast(db_session, abnb_id, publisher.id)
            make_report(db_session, f.id, error)
        result = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        assert result.significant == (result.p_value is not None and result.p_value < 0.05)

    def test_p_value_none_when_selected_has_fewer_than_2(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        result = AnalyticsService().get_distribution(db_session, ticker="AAPL")
        assert result.p_value is None
        assert result.significant is False


class TestAnalyticsServicePublisherFilter:
    def test_publisher_filter_returns_only_matching_errors(
        self, db_session: Session, aapl_id: int
    ) -> None:
        p1 = make_publisher(db_session, "Bank A")
        p2 = make_publisher(db_session, "Bank B")
        f1 = make_forecast(db_session, aapl_id, p1.id)
        f2 = make_forecast(db_session, aapl_id, p2.id)
        make_report(db_session, f1.id, 0.05)
        make_report(db_session, f2.id, -0.20)
        result = AnalyticsService().get_distribution(db_session, publisher_id=p1.id)
        assert sum(result.selected) == 1
        assert result.selected[10] == 1

    def test_unknown_publisher_returns_empty_selected(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        make_report(db_session, f.id, 0.05)
        result = AnalyticsService().get_distribution(db_session, publisher_id=99999)
        assert result.selected == [0] * 20


# ── Route tests ───────────────────────────────────────────────────────────────


class TestAnalyticsRoute:
    def test_no_filter_returns_200(self, client: object) -> None:
        response = client.get("/analytics/distribution")
        assert response.status_code == 200

    def test_response_has_required_fields(self, client: object) -> None:
        data = client.get("/analytics/distribution").json()
        for field in (
            "bins",
            "all",
            "selected",
            "mean_all",
            "mean_selected",
            "significant",
            "p_value",
        ):
            assert field in data

    def test_bins_field_correct(self, client: object) -> None:
        data = client.get("/analytics/distribution").json()
        assert data["bins"] == [
            -1.00, -0.90, -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, -0.20, -0.10,
             0.00,  0.10,  0.20,  0.30,  0.40,  0.50,  0.60,  0.70,  0.80,  0.90,  1.00,
        ]

    def test_both_ticker_and_publisher_id_returns_422(self, client: object) -> None:
        response = client.get("/analytics/distribution?ticker=AAPL&publisher_id=1")
        assert response.status_code == 422

    def test_ticker_filter_accepted(self, client: object) -> None:
        response = client.get("/analytics/distribution?ticker=AAPL")
        assert response.status_code == 200

    def test_publisher_id_filter_accepted(self, client: object) -> None:
        response = client.get("/analytics/distribution?publisher_id=1")
        assert response.status_code == 200

    def test_bin_counts_length_is_20(self, client: object) -> None:
        data = client.get("/analytics/distribution").json()
        assert len(data["all"]) == 20
        assert len(data["selected"]) == 20

    def test_empty_db_returns_zero_counts(self, client: object) -> None:
        data = client.get("/analytics/distribution").json()
        assert data["all"] == [0] * 20
        assert data["selected"] == [0] * 20

    def test_reports_endpoint_returns_page_payload(self, client: object) -> None:
        response = client.get("/analytics/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] == 0

    def test_reports_endpoint_rejects_both_filters(self, client: object) -> None:
        response = client.get("/analytics/reports?ticker=AAPL&publisher_id=1")
        assert response.status_code == 422

    def test_reports_endpoint_rejects_invalid_page(self, client: object) -> None:
        response = client.get("/analytics/reports?page=0")
        assert response.status_code == 422

    def test_reports_endpoint_rejects_invalid_page_size(self, client: object) -> None:
        response = client.get("/analytics/reports?page_size=101")
        assert response.status_code == 422
