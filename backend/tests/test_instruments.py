from fastapi.testclient import TestClient


def test_list_instruments(client: TestClient) -> None:
    response = client.get("/instruments/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    tickers = {item["ticker"] for item in data}
    assert tickers == {"AAPL", "ABNB"}


def test_get_instrument(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    instrument_id = instruments[0]["id"]

    response = client.get(f"/instruments/{instrument_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == instrument_id
    assert data["ticker"] == instruments[0]["ticker"]
    assert data["currency"] == "USD"


def test_get_instrument_not_found(client: TestClient) -> None:
    response = client.get("/instruments/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Instrument not found"


def test_delete_instrument(client: TestClient) -> None:
    instruments = client.get("/instruments/").json()
    instrument_id = instruments[0]["id"]

    response = client.delete(f"/instruments/{instrument_id}")
    assert response.status_code == 204

    confirm = client.get(f"/instruments/{instrument_id}")
    assert confirm.status_code == 404


def test_delete_instrument_not_found(client: TestClient) -> None:
    response = client.delete("/instruments/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Instrument not found"
