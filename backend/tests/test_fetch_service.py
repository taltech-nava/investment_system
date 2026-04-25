from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel import select

from src.models.instrument import Instrument
from src.models.instrument_class import InstrumentClass
from src.models.publisher import Publisher
from src.models.source import Source
from src.services.fetch_service import FetchService
from src.clients.serper_client import SerperClient

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(InstrumentClass(id=1, name="Stock"))
        session.commit()
        session.add(Instrument(class_id=1, ticker="AAPL", name="Apple Inc.", currency="USD"))
        session.commit()

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


def test_fetch_ticker_saves_source_to_database(session: Session) -> None:
    mock_serper_response = MagicMock()
    mock_serper_response.raise_for_status.return_value = None
    mock_serper_response.json.return_value = {
        "organic": [
            {
                "title": "Apple price target raised to $250",
                "link": "https://example.com/aapl",
                "snippet": "Analyst raises AAPL price target.",
                "date": "Jan 15, 2025",
            }
        ]
    }

    with patch("src.clients.serper_client.FetcherSettings") as mock_cfg:
        mock_cfg.return_value.serper_api_key = "test-key"
        mock_cfg.return_value.serper_max_results = 10
        mock_cfg.return_value.serper_period = "qdr:w"
        serper_client = SerperClient()

    with patch("src.clients.serper_client.requests.post", return_value=mock_serper_response):
        service = FetchService(session=session, serper_client=serper_client)
        service.fetch_ticker("AAPL")

    sources = session.exec(select(Source)).all()
    assert len(sources) == 1
    assert sources[0].file_path == "https://example.com/aapl"


def test_fetch_ticker_raises_for_unknown_ticker(session: Session) -> None:
    serper_client = MagicMock(spec=SerperClient)
    service = FetchService(session=session, serper_client=serper_client)

    with pytest.raises(ValueError, match="not found"):
        service.fetch_ticker("FAKE")