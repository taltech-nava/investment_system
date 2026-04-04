from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database.session import get_session
from main import app
from src.models.instrument import Instrument
from src.models.instrument_class import InstrumentClass

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture()
def setup_db() -> Generator[None, None, None]:
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(InstrumentClass(id=1, name="Stock"))
        session.commit()
        session.add_all(
            [
                Instrument(class_id=1, ticker="AAPL", name="APPLE INC.", currency="USD"),
                Instrument(class_id=1, ticker="ABNB", name="AIRBNB, INC CL A CMN", currency="USD"),
            ]
        )
        session.commit()

    yield

    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client(setup_db: None) -> TestClient:
    return TestClient(app)
