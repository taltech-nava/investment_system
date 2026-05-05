"""Tests for ReportService: report generation, metric calculations, skip logic."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, select

from src.models.forecast import Forecast
from src.models.instrument import Instrument
from src.models.publisher import Publisher
from src.models.report import Report
from src.services.report_service import ReportService

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_publisher(session: Session) -> Publisher:
    p = Publisher(institution="Test Bank")
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def make_forecast(
    session: Session,
    instrument_id: int,
    publisher_id: int,
    predicted_price: float | None = 120.0,
    spot_price: float | None = 100.0,
    maturation_date: date | None = None,
) -> Forecast:
    f = Forecast(
        instrument_id=instrument_id,
        publisher_id=publisher_id,
        prediction_date=date.today() - timedelta(days=365),
        maturation_date=maturation_date or (date.today() - timedelta(days=1)),
        predicted_price=Decimal(str(predicted_price)) if predicted_price is not None else None,
        currency="USD",
        spot_price_at_prediction=Decimal(str(spot_price)) if spot_price is not None else None,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


def make_service(actual_price: float | None) -> ReportService:
    mock_yf = MagicMock()
    mock_yf.fetch_realised_price.return_value = actual_price
    return mock_yf


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def aapl_id(db_session: Session) -> int:
    return db_session.exec(select(Instrument).where(Instrument.ticker == "AAPL")).first().id


@pytest.fixture()
def publisher(db_session: Session) -> Publisher:
    return make_publisher(db_session)


# ── price_return_error ────────────────────────────────────────────────────────


class TestPriceReturnError:
    def test_predicted_above_actual(self, db_session: Session, aapl_id: int, publisher: Publisher) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=110.0, spot_price=None)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 100.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report is not None
        # (110 - 100) / 100 = 0.1
        assert report.price_return_error == pytest.approx(Decimal("0.1"), abs=Decimal("0.0001"))

    def test_predicted_below_actual(self, db_session: Session, aapl_id: int, publisher: Publisher) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=90.0, spot_price=None)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 100.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        # (90 - 100) / 100 = -0.1
        assert report.price_return_error == pytest.approx(Decimal("-0.1"), abs=Decimal("0.0001"))

    def test_perfect_prediction(self, db_session: Session, aapl_id: int, publisher: Publisher) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=100.0, spot_price=None)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 100.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.price_return_error == pytest.approx(Decimal("0.0"), abs=Decimal("0.0001"))


# ── direction_correct ─────────────────────────────────────────────────────────


class TestDirectionCorrect:
    def test_bullish_prediction_price_goes_up(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # spot=100, predicted=120 (bullish), actual=110 (up) → correct
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=120.0, spot_price=100.0)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 110.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.direction_correct is True

    def test_bullish_prediction_price_goes_down(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # spot=100, predicted=120 (bullish), actual=90 (down) → wrong
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=120.0, spot_price=100.0)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 90.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.direction_correct is False

    def test_bearish_prediction_price_goes_down(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # spot=100, predicted=80 (bearish), actual=85 (down) → correct
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=80.0, spot_price=100.0)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 85.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.direction_correct is True

    def test_bearish_prediction_price_goes_up(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        # spot=100, predicted=80 (bearish), actual=115 (up) → wrong
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=80.0, spot_price=100.0)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 115.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.direction_correct is False

    def test_none_when_no_spot_price(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=120.0, spot_price=None)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 110.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.direction_correct is None


# ── Skip logic ────────────────────────────────────────────────────────────────


class TestSkipLogic:
    def test_no_report_when_price_unavailable(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = None
        written = ReportService(db_session, yf).generate_reports()
        assert written == 0
        assert db_session.exec(select(Report)).first() is None

    def test_forecast_not_yet_matured_is_skipped(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(
            db_session, aapl_id, publisher.id,
            maturation_date=date.today() + timedelta(days=10),
        )
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 110.0
        written = ReportService(db_session, yf).generate_reports()
        assert written == 0

    def test_forecast_with_existing_report_is_skipped(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        f = make_forecast(db_session, aapl_id, publisher.id)
        existing = Report(
            forecast_id=f.id,
            review_date=date.today(),
            actual_price=Decimal("110"),
            price_return_error=Decimal("0.1"),
        )
        db_session.add(existing)
        db_session.commit()
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 110.0
        written = ReportService(db_session, yf).generate_reports()
        assert written == 0
        assert len(db_session.exec(select(Report)).all()) == 1

    def test_forecast_with_null_predicted_price_is_skipped(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=None)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 110.0
        written = ReportService(db_session, yf).generate_reports()
        assert written == 0


# ── Bulk behaviour ────────────────────────────────────────────────────────────


class TestBulkBehaviour:
    def test_writes_one_report_per_mature_forecast(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=110.0)
        make_forecast(db_session, aapl_id, publisher.id, predicted_price=120.0)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 100.0
        written = ReportService(db_session, yf).generate_reports()
        assert written == 2
        assert len(db_session.exec(select(Report)).all()) == 2

    def test_review_date_is_today(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 100.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.review_date == date.today()

    def test_actual_price_stored(
        self, db_session: Session, aapl_id: int, publisher: Publisher
    ) -> None:
        make_forecast(db_session, aapl_id, publisher.id)
        yf = MagicMock()
        yf.fetch_realised_price.return_value = 105.0
        ReportService(db_session, yf).generate_reports()
        report = db_session.exec(select(Report)).first()
        assert report.actual_price == pytest.approx(Decimal("105.0"), abs=Decimal("0.0001"))
