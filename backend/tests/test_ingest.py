from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestIngestYfinance:
    def test_returns_404_for_unknown_ticker(self, client: TestClient) -> None:
        response = client.post("/ingest/yfinance/UNKNOWN")

        assert response.status_code == 404
        assert "UNKNOWN" in response.json()["detail"]

    def test_saves_forecasts_and_price(self, client: TestClient) -> None:
        today = date.today()
        targets = [
            {
                "ticker": "AAPL",
                "firm": "Goldman Sachs",
                "grade_date": today - timedelta(days=30),
                "maturation_date": today + timedelta(days=335),
                "price_target": 200.0,
                "to_grade": "Buy",
                "from_grade": "Neutral",
            }
        ]
        with (
            patch("routes.ingest.yfinance_service.fetch_analyst_targets", return_value=targets),
            patch("routes.ingest.yfinance_service.fetch_realised_price", return_value=150.0),
        ):
            response = client.post("/ingest/yfinance/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["forecasts_saved"] == 1
        assert data["prices_saved"] == 1

    def test_skips_duplicate_forecast(self, client: TestClient) -> None:
        today = date.today()
        targets = [
            {
                "ticker": "AAPL",
                "firm": "Goldman Sachs",
                "grade_date": today - timedelta(days=30),
                "maturation_date": today + timedelta(days=335),
                "price_target": 200.0,
                "to_grade": "Buy",
                "from_grade": "Neutral",
            }
        ]
        with (
            patch("routes.ingest.yfinance_service.fetch_analyst_targets", return_value=targets),
            patch("routes.ingest.yfinance_service.fetch_realised_price", return_value=150.0),
        ):
            client.post("/ingest/yfinance/AAPL")
            response = client.post("/ingest/yfinance/AAPL")

        assert response.json()["forecasts_saved"] == 0
        assert response.json()["prices_saved"] == 0

    def test_saves_zero_when_no_targets_returned(self, client: TestClient) -> None:
        with (
            patch("routes.ingest.yfinance_service.fetch_analyst_targets", return_value=[]),
            patch("routes.ingest.yfinance_service.fetch_realised_price", return_value=None),
        ):
            response = client.post("/ingest/yfinance/AAPL")

        assert response.status_code == 200
        assert response.json()["forecasts_saved"] == 0
        assert response.json()["prices_saved"] == 0
