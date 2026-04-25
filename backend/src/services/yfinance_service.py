from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class YFinanceService:
    # --- FETCH PRICE PREDICTIOMS ---

    def fetch_analyst_targets(self, tickers: list[str]) -> list[dict]:
        """
        For each ticker, fetches analyst upgrades/downgrades from yfinance.
        Filters to records from the last 12 months.
        Skips rows without a price target.

        Returns a list of dicts shaped for the forecast_prices table.
        """
        cutoff: date = date.today() - timedelta(days=365)
        results: list[dict] = []

        for ticker in tickers:
            logger.info("Fetching analyst targets for %s", ticker)
            try:
                df: pd.DataFrame = yf.Ticker(ticker).get_upgrades_downgrades()
                if df is None or df.empty:
                    continue

                df = df[df.index.date >= cutoff]
                if df.empty:
                    continue

                for grade_date, row in df.iterrows():
                    price_target = row.get("currentPriceTarget")
                    if pd.isna(price_target):
                        continue
                    gd: date = grade_date.date()
                    results.append(
                        {
                            "ticker": ticker,
                            "firm": row.get("Firm"),
                            "grade_date": gd,
                            "maturation_date": gd + timedelta(days=365),
                            "price_target": float(price_target),
                            "to_grade": row.get("ToGrade"),
                            "from_grade": row.get("FromGrade"),
                        }
                    )
            except Exception as e:
                logger.warning("Error fetching analyst targets for %s: %s", ticker, e)

        return results

    # --- FETCH REALISED PRICE ---

    def fetch_realised_price(self, ticker: str, target_date: date) -> float | None:
        """
        Fetches the closing price for a ticker on a specific date; to enssure price is fetched also for dates when the market is closed, a 5 day window is used, and the nearest next date price is fetched.
        Returns None if no data is available for the 5-day window.

        Shaped for the realised_prices table.
        """
        try:
            hist: pd.DataFrame = yf.Ticker(ticker).history(
                start=target_date,
                end=target_date + timedelta(days=5),
            )
            if hist.empty:
                logger.warning("No price data for %s on %s", ticker, target_date)
                return None
            return float(hist["Close"].iloc[0])
        except Exception as e:
            logger.warning("Error fetching realised price for %s: %s", ticker, e)
            return None
