from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pandas as pd
import pytest

from src.services.yfinance_service import YFinanceService


@pytest.fixture
def service() -> YFinanceService:
    return YFinanceService()


def make_upgrades_df(price_target: float, days_ago: int = 30) -> pd.DataFrame:
    grade_date = pd.Timestamp(date.today() - timedelta(days=days_ago))
    return pd.DataFrame(
        {
            "Firm": ["Goldman Sachs"],
            "ToGrade": ["Buy"],
            "FromGrade": ["Neutral"],
            "currentPriceTarget": [price_target],
        },
        index=[grade_date],
    )


class TestFetchAnalystTargets:
    def test_returns_results_for_valid_data(self, service: YFinanceService) -> None:
        df = make_upgrades_df(price_target=200.0)
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = df
            results = service.fetch_analyst_targets(["AAPL"])

        assert len(results) == 1
        assert results[0]["ticker"] == "AAPL"
        assert results[0]["firm"] == "Goldman Sachs"
        assert results[0]["price_target"] == 200.0
        assert results[0]["to_grade"] == "Buy"
        assert results[0]["from_grade"] == "Neutral"
        assert results[0]["maturation_date"] == results[0]["grade_date"] + timedelta(days=365)

    def test_skips_rows_with_missing_price_target(self, service: YFinanceService) -> None:
        df = make_upgrades_df(price_target=float("nan"))
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = df
            results = service.fetch_analyst_targets(["AAPL"])

        assert results == []

    def test_skips_ticker_with_empty_dataframe(self, service: YFinanceService) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = pd.DataFrame()
            results = service.fetch_analyst_targets(["AAPL"])

        assert results == []

    def test_skips_ticker_with_none_response(self, service: YFinanceService) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = None
            results = service.fetch_analyst_targets(["AAPL"])

        assert results == []

    def test_filters_out_results_older_than_12_months(self, service: YFinanceService) -> None:
        df = make_upgrades_df(price_target=200.0, days_ago=400)
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = df
            results = service.fetch_analyst_targets(["AAPL"])

        assert results == []

    def test_handles_api_exception_gracefully(self, service: YFinanceService) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.side_effect = Exception("API error")
            results = service.fetch_analyst_targets(["AAPL"])

        assert results == []

    def test_processes_multiple_tickers(self, service: YFinanceService) -> None:
        df = make_upgrades_df(price_target=200.0)
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.get_upgrades_downgrades.return_value = df
            results = service.fetch_analyst_targets(["AAPL", "MSFT"])

        assert len(results) == 2
        tickers = {r["ticker"] for r in results}
        assert tickers == {"AAPL", "MSFT"}


class TestFetchRealisedPrice:
    def test_returns_first_closing_price(self, service: YFinanceService) -> None:
        df = pd.DataFrame({"Close": [150.0, 151.0]})
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = df
            result = service.fetch_realised_price("AAPL", date.today())

        assert result == 150.0

    def test_returns_none_for_empty_history(self, service: YFinanceService) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = service.fetch_realised_price("AAPL", date.today())

        assert result is None

    def test_returns_none_on_exception(self, service: YFinanceService) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("Network error")
            result = service.fetch_realised_price("AAPL", date.today())

        assert result is None

    def test_fetches_5_day_window(self, service: YFinanceService) -> None:
        target_date = date(2025, 1, 1)
        df = pd.DataFrame({"Close": [150.0]})
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = df
            service.fetch_realised_price("AAPL", target_date)
            _, kwargs = mock_ticker.return_value.history.call_args
            assert kwargs["start"] == target_date
            assert kwargs["end"] == target_date + timedelta(days=5)
