from fastapi.testclient import TestClient


def test_list_publishers_empty(client: TestClient) -> None:
    response = client.get("/publishers/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_publishers_returns_created_items(client: TestClient) -> None:
    # Create publishers through forecast endpoint where publisher_name is normalized.
    payload = {
        "instrument_id": 1,
        "publisher_name": "Alpha Research",
        "scenario": "single",
        "predicted_price": 100.0,
        "maturation_date": "2027-01-01",
        "conviction": 4,
        "conviction_source": "manual",
        "horizon_source": "source_declared",
        "method": "Manual entry",
        "entry_mode": "manual",
        "estimate_type": "manual_point_estimate",
    }
    response = client.post("/forecasts", json=payload)
    assert response.status_code == 201

    publishers_response = client.get("/publishers/")
    assert publishers_response.status_code == 200

    data = publishers_response.json()
    assert any(item["institution"] == "Alpha Research" for item in data)
