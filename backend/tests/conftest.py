import os

# Must be set before any app imports trigger pydantic-settings validation
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("DB_HOST", "localhost")

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database.session import get_session
from main import app
from src.models.aggregate_component import AggregateComponent  # noqa: F401
from src.models.forecast import Forecast  # noqa: F401
from src.models.forecast_aggregate import ForecastAggregate  # noqa: F401
from src.models.forecast_source import ForecastSource  # noqa: F401
from src.models.instrument import Instrument
from src.models.instrument_class import InstrumentClass
from src.models.price import Price  # noqa: F401
from src.models.publisher import Publisher  # noqa: F401
from src.models.report import Report  # noqa: F401
from src.models.source import Source  # noqa: F401
from src.models.source_input import SourceInput  # noqa: F401

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


@pytest.fixture()
def db_session(setup_db: None) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
