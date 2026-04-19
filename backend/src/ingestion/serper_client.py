#serper_client.py backend/src/services/fetcher/

#Makes the HTTP call to Serper. Returns a list of RawResult objects

"""Serper search client.

Returns a list of RawResult dataclasses — engine-agnostic structs that
FetchService maps to Source / Publisher ORM objects.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

import requests
import trafilatura

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/search"


@dataclass
class RawResult:
    engine: str                    # "serper"
    ticker: str
    query: str
    title: str | None
    url: str | None
    snippet: str | None            # short excerpt returned by Serper
    #full_text: str | None          # full article body extracted by trafilatura
    published_date: date | None    # parsed from Serper's date field where available
    authors: list[str] = field(default_factory=list)
    fetch_date: date = field(default_factory=date.today)


class SerperClient:
    def __init__(self) -> None:
        cfg = FetcherSettings()
        self._api_key = cfg.serper_api_key
        self._max_results = cfg.serper_max_results
        self._period = cfg.serper_period

    def search(self, ticker: str, query: str) -> list[RawResult]:
        """Run one Serper query and return a list of RawResult objects."""
        payload = {
            "q": query,
            "num": self._max_results,
            "tbs": self._period,
        }
        headers = {
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(_SERPER_URL, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Serper request failed for ticker=%s: %s", ticker, exc)
            return []

        data = response.json()
        return [
            self._map_result(ticker, query, item)
            for item in data.get("organic", [])
        ]

    @staticmethod
    def _fetch_full_text(url: str) -> str | None:
        """Fetch the page and extract article body via trafilatura."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return trafilatura.extract(response.text) or None
        except Exception as exc:
            logger.debug("Full-text fetch failed for %s: %s", url, exc)
            return None

    @staticmethod
    def _parse_date(raw: str | None) -> date | None:
        if not raw:
            return None
        from dateutil import parser as dateparser
        try:
            return dateparser.parse(raw, fuzzy=True).date()
        except Exception:
            return None

    def _map_result(self, ticker: str, query: str, item: dict) -> RawResult:
        url = item.get("link")
        return RawResult(
            engine="serper",
            ticker=ticker,
            query=query,
            title=item.get("title"),
            url=url,
            snippet=item.get("snippet"),
            #full_text=self._fetch_full_text(url) if url else None,
            published_date=self._parse_date(item.get("date")),
            fetch_date=date.today(),
        )


if __name__ == "__main__":
    import os
    from config.fetcher import FetcherSettings

    cfg = FetcherSettings()
    client = SerperClient(
        api_key=cfg.serper_api_key,
        max_results=cfg.serper_max_results,
        period=cfg.serper_period,
    )

    ticker = "AAPL"
    query = f'{ticker} stock "price target" (raises OR raised OR upgrade OR downgrade OR outlook)'

    results = client.search(ticker, query)

    for r in results:
        print("TITLE:", r.title)
        print("URL:  ", r.url)
        print("DATE: ", r.published_date)
        print("SNIPPET:", r.snippet)
        #print("TEXT:", r.full_text)
        print("-" * 50)