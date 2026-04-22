from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from collections.abc import Generator

from src.models.instrument import Instrument
from src.models.instrument_class import InstrumentClass
from src.models.price import Price
from src.repositories.price_repository import PriceRepository


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
    session.commit()
    return session


@pytest.fixture
def repo() -> PriceRepository:
    return PriceRepository()


def make_price(
    instrument_id: int = 1, price_date: date = date(2025, 1, 1), price: float = 150.0
) -> Price:
    return Price(
        instrument_id=instrument_id,
        price_date=price_date,
        price=Decimal(str(price)),
        currency="USD",
        data_source="yfinance",
    )


class TestSave:
    def test_saves_price_and_returns_with_id(
        self, seeded_session: Session, repo: PriceRepository
    ) -> None:
        price = make_price()
        saved = repo.save(seeded_session, price)

        assert saved.id is not None
        assert saved.price == Decimal("150.0")
        assert saved.data_source == "yfinance"


class TestGetByInstrumentAndDate:
    def test_returns_price_when_found(self, seeded_session: Session, repo: PriceRepository) -> None:
        repo.save(seeded_session, make_price(price_date=date(2025, 1, 1)))
        result = repo.get_by_instrument_and_date(
            seeded_session, instrument_id=1, price_date=date(2025, 1, 1)
        )

        assert result is not None
        assert result.price_date == date(2025, 1, 1)

    def test_returns_none_when_not_found(
        self, seeded_session: Session, repo: PriceRepository
    ) -> None:
        result = repo.get_by_instrument_and_date(
            seeded_session, instrument_id=1, price_date=date(2025, 1, 1)
        )

        assert result is None

    def test_returns_none_for_different_date(
        self, seeded_session: Session, repo: PriceRepository
    ) -> None:
        repo.save(seeded_session, make_price(price_date=date(2025, 1, 1)))
        result = repo.get_by_instrument_and_date(
            seeded_session, instrument_id=1, price_date=date(2025, 6, 1)
        )

        assert result is None
