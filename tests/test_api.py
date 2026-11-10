import pytest
from fastapi.testclient import TestClient

import api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "api-test.db")
    with TestClient(api.app) as test_client:
        yield test_client


def _payload():
    return {
        "factory_name": "API Test Factory",
        "city": "Mangaluru",
        "state": "Karnataka",
        "monthly_capacity": 2500,
        "capacity_unit": "Units",
        "machines": ["CNC Lathe"],
        "processes": ["Turning"],
        "materials": ["Aluminium"],
        "certifications": ["ISO 9001"],
    }


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_factory_crud_endpoints(client):
    created = client.post("/factories", json=_payload())
    assert created.status_code == 201
    factory_id = created.json()["id"]
    assert created.json()["factory_name"] == "API Test Factory"

    listed = client.get("/factories?search=Mangaluru")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    read = client.get(f"/factories/{factory_id}")
    assert read.status_code == 200

    changed_payload = _payload()
    changed_payload["factory_name"] = "Updated API Factory"
    changed_payload["city"] = "Udupi"
    updated = client.put(f"/factories/{factory_id}", json=changed_payload)
    assert updated.status_code == 200
    assert updated.json()["factory_name"] == "Updated API Factory"
    assert updated.json()["city"] == "Udupi"

    deleted = client.delete(f"/factories/{factory_id}")
    assert deleted.status_code == 200
    assert client.get(f"/factories/{factory_id}").status_code == 404


def test_invalid_factory_payload_is_rejected(client):
    payload = _payload()
    payload["monthly_capacity"] = 0
    response = client.post("/factories", json=payload)
    assert response.status_code == 422


def test_missing_factory_returns_404(client):
    response = client.get("/factories/999")
    assert response.status_code == 404
