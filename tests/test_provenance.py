import pytest
from fastapi.testclient import TestClient

import api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "review-api.db")
    with TestClient(api.app) as test_client:
        created = test_client.post(
            "/factories",
            json={
                "factory_name": "Review Test Factory",
                "city": "Mangaluru",
                "state": "Karnataka",
                "monthly_capacity": 1200,
                "capacity_unit": "Units",
                "machines": ["CNC Lathe"],
                "processes": ["Turning"],
                "materials": ["Steel"],
                "certifications": [],
            },
        )
        assert created.status_code == 201
        test_client.factory_id = created.json()["id"]
        yield test_client


def test_review_defaults_to_unverified(client):
    response = client.get(f"/factories/{client.factory_id}/review")
    assert response.status_code == 200
    assert response.json()["verification_status"] == "Unverified"
    assert response.json()["data_source"] == "Factory self-report"


def test_save_and_read_review_metadata(client):
    payload = {
        "data_source": "Supplier-provided capability sheet",
        "verification_status": "Evidence attached",
        "evidence_reference": "docs/capability-sheet-001.pdf",
        "reviewed_by": "Procurement team",
    }
    saved = client.put(f"/factories/{client.factory_id}/review", json=payload)
    assert saved.status_code == 200
    assert saved.json()["data_source"] == payload["data_source"]
    assert saved.json()["verification_status"] == "Evidence attached"

    fetched = client.get(f"/factories/{client.factory_id}/review")
    assert fetched.status_code == 200
    assert fetched.json()["evidence_reference"] == payload["evidence_reference"]
    assert fetched.json()["reviewed_by"] == payload["reviewed_by"]


def test_review_unknown_factory_returns_404(client):
    response = client.get("/factories/99999/review")
    assert response.status_code == 404


def test_invalid_review_status_is_rejected(client):
    response = client.put(
        f"/factories/{client.factory_id}/review",
        json={
            "data_source": "Factory self-report",
            "verification_status": "Verified by AI",
            "evidence_reference": "",
            "reviewed_by": "",
        },
    )
    assert response.status_code == 422
