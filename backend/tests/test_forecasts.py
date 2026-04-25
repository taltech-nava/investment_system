from conftest import engine
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.models.forecast import Forecast
from src.models.publisher import Publisher


def test_get_forecast_settings(client: TestClient) -> None:
    response = client.get("/forecasts/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["estimate_types"]
    assert data["scenarios"] == ["bear", "base", "bull", "single"]


def test_create_forecast(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": "Goldman Sachs",
        "scenario": "base",
        "predicted_price": 180.0,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Macro desk consensus",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["scenario"] == "base"
    assert data["predicted_price"] == "180.0000"
    assert data["conviction_source"] == "manual"
    assert data["horizon_source"] == "source_declared"
    assert data["entry_mode"] == "manual"
    assert data["estimate_type"] == "manual_point_estimate"


def test_create_forecast_without_publisher_uses_self(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": None,
        "scenario": "single",
        "predicted_price": 210.5,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Manual entry",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 201

    with Session(engine) as session:
        publisher = session.exec(select(Publisher).where(Publisher.institution == "Self")).first()
        assert publisher is not None

        forecasts = session.exec(
            select(Forecast).where(Forecast.publisher_id == publisher.id)
        ).all()
        assert len(forecasts) == 1
        assert forecasts[0].scenario == "single"


def test_create_forecast_unsupported_scenario_returns_422(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": "Analyst Desk",
        "scenario": "extreme_bull",
        "predicted_price": 220.5,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Model",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 422


def test_create_forecast_unsupported_estimate_type_returns_422(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": "Analyst Desk",
        "scenario": "base",
        "predicted_price": 220.5,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Model",
        "entry_mode": "manual",
        "estimate_type": "invalid_type",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 422


def test_create_forecast_rejects_predicted_price_out_of_bounds(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": "Analyst Desk",
        "scenario": "base",
        "predicted_price": 100000000.0,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Model",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 422


def test_create_forecast_rejects_blank_required_text_fields(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    payload = {
        "instrument_id": instruments[0]["id"],
        "publisher_name": "Analyst Desk",
        "scenario": "base",
        "predicted_price": 220.5,
        "maturation_date": "2099-01-01",
        "conviction": 4,
        "conviction_source": "   ",
        "horizon_source": "source_declared",
        "method": "Model",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }

    response = client.post("/forecasts", json=payload)

    assert response.status_code == 422
