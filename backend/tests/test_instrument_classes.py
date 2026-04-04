from fastapi.testclient import TestClient


def test_list_instrument_classes(client: TestClient) -> None:
    response = client.get("/instrument-classes/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    names = {item["name"] for item in data}
    assert names == {"Stock"}


def test_get_instrument_class(client: TestClient) -> None:
    instrument_classes = client.get("/instrument-classes/").json()
    instrument_class_id = instrument_classes[0]["id"]

    response = client.get(f"/instrument-classes/{instrument_class_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == instrument_class_id
    assert data["name"] == instrument_classes[0]["name"]


def test_get_instrument_class_not_found(client: TestClient) -> None:
    response = client.get("/instrument-classes/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Instrument class not found"
