#fetch_sources.py backend/scripts/

#CLI entry point. Run this directly. Wires config → clients → service → DB

#!/usr/bin/env python
"""Fetch price-target sources for NASDAQ100 tickers via Serper and persist them.

Usage (from backend/ directory):
    uv run python scripts/fetch_sources.py
    uv run python scripts/fetch_sources.py --ticker AAPL
    uv run python scripts/fetch_sources.py --dry-run

Environment variables (via .env or shell):
    SERPER_API_KEY  — required
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.fetcher import FetcherSettings  # noqa: E402
from database.session import get_session    # noqa: E402
#from src.services.fetcher import FetchService, SerperClient  # noqa: E402
from src.ingestion import FetchService, SerperClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fetch_sources")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch NASDAQ100 price-target sources via Serper.")
    parser.add_argument("--ticker", help="Fetch a single ticker instead of all NASDAQ100.")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit.")
    args = parser.parse_args()

    cfg = FetcherSettings()

    logger.info("Query template: %s", cfg.query_template)
    logger.info("Max results per ticker: %d  |  Period: %s", cfg.serper_max_results, cfg.serper_period)

    if args.dry_run:
        logger.info("Dry-run mode — exiting without fetching.")
        return

    if not cfg.serper_api_key:
        logger.error("SERPER_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    serper = SerperClient(
        api_key=cfg.serper_api_key,
        max_results=cfg.serper_max_results,
        period=cfg.serper_period,
    )

    session_gen = get_session()
    session = next(session_gen)

    try:
        service = FetchService(session=session, serper_client=serper, query_template=cfg.query_template)

        if args.ticker:
            n = service.fetch_ticker(args.ticker.upper())
            logger.info("Saved %d records for ticker=%s", n, args.ticker.upper())
        else:
            summary = service.fetch_all_nasdaq100()
            logger.info("Done. %s", summary)
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


if __name__ == "__main__":
    main()