from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from collections.abc import Generator

from src.models.forecast import Forecast
from src.models.instrument import Instrument
from src.models.instrument_class import InstrumentClass
from src.models.publisher import Publisher
from src.repositories.forecast_repository import ForecastRepository


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def seeded_session(session: Session) -> Session:
    session.add(InstrumentClass(id=1, name="Stock"))
    session.commit()
    session.add(Instrument(id=1, class_id=1, ticker="AAPL", name="Apple Inc.", currency="USD"))
    session.add(Publisher(id=1, institution="Goldman Sachs"))
    session.commit()
    return session


@pytest.fixture
def repo() -> ForecastRepository:
    return ForecastRepository()


def make_forecast(
    instrument_id: int = 1, publisher_id: int = 1, prediction_date: date = date(2025, 1, 1)
) -> Forecast:
    return Forecast(
        instrument_id=instrument_id,
        publisher_id=publisher_id,
        prediction_date=prediction_date,
        maturation_date=date(2026, 1, 1),
        predicted_price=Decimal("200.00"),
        extracted_raw_price=Decimal("200.00"),
        currency="USD",
    )


class TestSave:
    def test_saves_forecast_and_returns_with_id(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        forecast = make_forecast()
        saved = repo.save(seeded_session, forecast)

        assert saved.id is not None
        assert saved.predicted_price == Decimal("200.00")
        assert saved.currency == "USD"


class TestExists:
    def test_returns_true_when_forecast_exists(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        repo.save(seeded_session, make_forecast())
        assert (
            repo.exists(
                seeded_session, instrument_id=1, publisher_id=1, prediction_date=date(2025, 1, 1)
            )
            is True
        )

    def test_returns_false_when_no_matching_forecast(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        assert (
            repo.exists(
                seeded_session, instrument_id=1, publisher_id=1, prediction_date=date(2025, 1, 1)
            )
            is False
        )

    def test_returns_false_for_different_date(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        repo.save(seeded_session, make_forecast(prediction_date=date(2025, 1, 1)))
        assert (
            repo.exists(
                seeded_session, instrument_id=1, publisher_id=1, prediction_date=date(2025, 6, 1)
            )
            is False
        )


class TestGetByInstrument:
    def test_returns_forecasts_for_instrument(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        repo.save(seeded_session, make_forecast(prediction_date=date(2025, 1, 1)))
        repo.save(seeded_session, make_forecast(prediction_date=date(2025, 3, 1)))
        results = repo.get_by_instrument(seeded_session, instrument_id=1)

        assert len(results) == 2

    def test_returns_forecasts_ordered_by_date_descending(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        repo.save(seeded_session, make_forecast(prediction_date=date(2025, 1, 1)))
        repo.save(seeded_session, make_forecast(prediction_date=date(2025, 6, 1)))
        results = repo.get_by_instrument(seeded_session, instrument_id=1)

        assert results[0].prediction_date == date(2025, 6, 1)
        assert results[1].prediction_date == date(2025, 1, 1)

    def test_returns_empty_list_when_no_forecasts(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        results = repo.get_by_instrument(seeded_session, instrument_id=1)
        assert results == []


class TestGetOrCreatePublisher:
    def test_creates_new_publisher_when_not_found(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        publisher = repo.get_or_create_publisher(seeded_session, "Morgan Stanley")

        assert publisher.id is not None
        assert publisher.institution == "Morgan Stanley"

    def test_returns_existing_publisher(
        self, seeded_session: Session, repo: ForecastRepository
    ) -> None:
        publisher1 = repo.get_or_create_publisher(seeded_session, "Goldman Sachs")
        publisher2 = repo.get_or_create_publisher(seeded_session, "Goldman Sachs")

        assert publisher1.id == publisher2.id
