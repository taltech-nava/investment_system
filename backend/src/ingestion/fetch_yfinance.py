from __future__ import annotations

import yfinance as yf
import pandas as pd
from datetime import date, timedelta


# --- 1. CONFIGURATION ---

NASDAQ_100_TICKERS: list[str] = [
    # full NASDAQ 100 list goes here
    "AAPL", "MSFT", "NVDA",
]


# --- 2. FETCH ANALYST PRICE TARGETS ---

def fetch_analyst_targets(tickers: list[str]) -> list[dict]:
    """
    For each ticker, fetches analyst upgrades/downgrades from yfinance.
    Filters to records from the last 12 months.
    Skips rows without a price target.

    Returns a list of dicts shaped for the forecast_prices table.
    """
    cutoff: date = date.today() - timedelta(days=365)
    results: list[dict] = []

    for ticker in tickers:
        print(f"   [Targets] {ticker}...", end="\r")
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
                results.append({
                    "ticker": ticker,
                    "firm": row.get("Firm"),
                    "grade_date": gd,
                    "maturation_date": gd + timedelta(days=365),
                    "price_target": float(price_target),
                    "to_grade": row.get("ToGrade"),
                    "from_grade": row.get("FromGrade"),
                })
        except Exception as e:
            print(f"   ! [{ticker}] Error fetching analyst targets: {e}")

    return results


# --- 3. FETCH REALISED PRICE ---

def fetch_realised_price(ticker: str, target_date: date) -> float | None:
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
            print(f"   ! [{ticker}] No price data for {target_date}")
            return None
        return float(hist["Close"].iloc[0])
    except Exception as e:
        print(f"   ! [{ticker}] Error fetching realised price: {e}")
        return None


# --- MAIN ---

if __name__ == "__main__":
    print(">>> Fetching analyst price targets for NASDAQ 100")
    #targets = fetch_analyst_targets(NASDAQ_100_TICKERS)
    #print(f"\n   Done. {len(targets)} analyst target records fetched.")
    for ticker in NASDAQ_100_TICKERS:
        print(f"TICKER: {ticker}")
        targets = fetch_analyst_targets([ticker])
        print(f"    The number of estimates for {ticker}: {len(targets)}")
        for t in targets[:5]:
            print(f"      {t}")

    print("\n>>> Fetching realised prices")
    #sample_ticker = NASDAQ_100_TICKERS[0]
    for ticker in NASDAQ_100_TICKERS:
        price = fetch_realised_price(ticker, date.today())
        print(f"   {ticker} closing price today: {price}")
