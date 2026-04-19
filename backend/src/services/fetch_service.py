#fetch_service.py backend/src/services/fetcher/

#Loops over all NASDAQ100 instruments, calls Serper, saves results to DB

from __future__ import annotations

import logging

from sqlmodel import Session

from src.models.instrument import Instrument
from src.models.publisher import Publisher
from src.models.source import Source
from src.repositories.instrument_repository import instrument_repository
from src.repositories.publisher_repository import publisher_repository
from src.repositories.source_repository import source_repository
from src.ingestion.serper_client import RawResult, SerperClient

logger = logging.getLogger(__name__)


class FetchService:
    def __init__(
        self,
        session: Session,
        serper_client: SerperClient,
        query_template: str = '{ticker} stock "price target" (raise OR lower OR upgrad OR downgrad OR outlook)',
    ) -> None:
        self._session = session
        self._serper = serper_client
        self._query_template = query_template

    def fetch_all_nasdaq100(self) -> dict[str, int]:
        instruments = instrument_repository.list_by_class(self._session, class_id=1)
        if not instruments:
            logger.warning("No instruments found for class_id=1. Aborting.")
            return {"fetched": 0, "errors": 0}

        summary = {"fetched": 0, "errors": 0}
        for instrument in instruments:
            try:
                summary["fetched"] += self._fetch_for_ticker(instrument)
            except Exception as exc:
                logger.error("Error for ticker=%s: %s", instrument.ticker, exc, exc_info=True)
                summary["errors"] += 1

        logger.info("Fetch complete. %s", summary)
        return summary

    def fetch_ticker(self, ticker: str) -> int:
        instrument = instrument_repository.get_by_ticker(self._session, ticker)
        if not instrument:
            raise ValueError(f"Ticker {ticker!r} not found.")
        return self._fetch_for_ticker(instrument)

    def _fetch_for_ticker(self, instrument: Instrument) -> int:
        query = self._query_template.format(ticker=instrument.ticker)
        results: list[RawResult] = self._serper.search(instrument.ticker, query)

        saved = 0
        for raw in results:
            try:
                self._persist_result(raw, instrument)
                saved += 1
            except Exception as exc:
                logger.warning("Failed to persist url=%s: %s", raw.url, exc)

        logger.info("ticker=%s saved=%d", instrument.ticker, saved)
        return saved

    def _persist_result(self, raw: RawResult, instrument: Instrument) -> Source:
        publisher = self._get_or_create_publisher(raw)

        # map RawResult → Source (without full_text)
        source = Source(publisher_id=publisher.id,
                        title=raw.title,
                        file_path=raw.url,
                        #content=raw.full_text,
						snippet_text=raw.snippet,
                        search_subjects=[instrument.ticker],
                        search_query_full=raw.query,
                        search_engine="serper",
                        horizon_context="convention_assigned",
                        mode="serper",
                        fetch_date=raw.fetch_date,
                        audit_status=None,
        )
        
        return source_repository.create(self._session, source)

    def _get_or_create_publisher(self, raw: RawResult) -> Publisher:
        if raw.url:
            existing = publisher_repository.get_by_url(self._session, raw.url)
            if existing:
                return existing

        publisher = Publisher(
            url=raw.url,
            title=raw.title,
            publication_date=raw.published_date,
            authors=raw.authors or [],
        )
        return publisher_repository.create(self._session, publisher)