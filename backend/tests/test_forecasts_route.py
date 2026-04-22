from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestGetForecasts:
    def test_returns_404_for_unknown_ticker(self, client: TestClient) -> None:
        response = client.get("/forecasts/UNKNOWN")

        assert response.status_code == 404
        assert "UNKNOWN" in response.json()["detail"]

    def test_returns_empty_list_when_no_forecasts(self, client: TestClient) -> None:
        response = client.get("/forecasts/AAPL")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_stored_forecasts(self, client: TestClient) -> None:
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
            patch("routes.ingest.yfinance_service.fetch_realised_price", return_value=None),
        ):
            client.post("/ingest/yfinance/AAPL")

        response = client.get("/forecasts/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["predicted_price"] == "200.0000"
        assert data[0]["currency"] == "USD"
