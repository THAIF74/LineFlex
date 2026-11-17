import pytest
from fastapi.testclient import TestClient

import api
from planning import add_production_requirement, delete_production_requirement
from requirement_versions import (
    get_requirement_version_history,
    update_production_requirement,
)


def _requirement(db_path, **overrides):
    values = {
        "requirement_name": "Housing Part A",
        "part_number": "HSG-A-001",
        "monthly_demand": 2500,
        "capacity_unit": "Units",
        "notes": "Initial planning note",
        "required_capabilities": {
            "Machine": ["CNC Lathe"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
        "db_path": db_path,
    }
    values.update(overrides)
    return add_production_requirement(**values)


def _update(db_path, requirement_id, **overrides):
    values = {
        "requirement_id": requirement_id,
        "requirement_name": "Housing Part A Rev B",
        "part_number": "HSG-A-001-B",
        "monthly_demand": 3000,
        "capacity_unit": "Units",
        "notes": "Updated planning note",
        "required_capabilities": {
            "Machine": ["CNC Lathe", "VMC"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
        "change_note": "Demand and machine requirements updated",
        "db_path": db_path,
    }
    values.update(overrides)
    return update_production_requirement(**values)


def test_existing_requirement_gets_initial_version(tmp_path):
    db = tmp_path / "versions.db"
    requirement_id = _requirement(db)
    history = get_requirement_version_history(requirement_id, db_path=db)
    assert len(history) == 1
    assert history[0]["version_number"] == 1
    assert history[0]["change_note"] == "Initial version"
    assert history[0]["snapshot"]["required_capabilities"]["Machine"] == ["CNC Lathe"]


def test_update_saves_new_version_and_preserves_previous_snapshot(tmp_path):
    db = tmp_path / "versions.db"
    requirement_id = _requirement(db)
    updated = _update(db, requirement_id)
    history = get_requirement_version_history(requirement_id, db_path=db)

    assert updated["requirement_name"] == "Housing Part A Rev B"
    assert updated["current_version"] == 2
    assert [item["version_number"] for item in history] == [2, 1]
    assert history[0]["snapshot"]["monthly_demand"] == 3000
    assert history[1]["snapshot"]["monthly_demand"] == 2500
    assert history[0]["change_note"] == "Demand and machine requirements updated"


def test_invalid_update_does_not_create_a_new_version(tmp_path):
    db = tmp_path / "versions.db"
    requirement_id = _requirement(db)
    with pytest.raises(ValueError):
        _update(db, requirement_id, monthly_demand=0)
    history = get_requirement_version_history(requirement_id, db_path=db)
    assert [item["version_number"] for item in history] == [1]


def test_change_note_is_required(tmp_path):
    db = tmp_path / "versions.db"
    requirement_id = _requirement(db)
    with pytest.raises(ValueError, match="change note"):
        _update(db, requirement_id, change_note="   ")


def test_missing_requirement_update_returns_none(tmp_path):
    db = tmp_path / "versions.db"
    assert _update(db, 999) is None


def test_delete_requirement_cascades_version_history(tmp_path):
    db = tmp_path / "versions.db"
    requirement_id = _requirement(db)
    get_requirement_version_history(requirement_id, db_path=db)
    assert delete_production_requirement(requirement_id, db_path=db) is True
    assert get_requirement_version_history(requirement_id, db_path=db) == []


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "api-versions.db")
    with TestClient(api.app) as client:
        yield client


def _api_payload():
    return {
        "requirement_name": "API Housing Requirement",
        "part_number": "API-H-01",
        "monthly_demand": 1800,
        "capacity_unit": "Units",
        "notes": "API version test",
        "required_capabilities": {
            "Machine": ["CNC Lathe"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
    }


def test_api_updates_requirement_and_returns_version_history(api_client):
    created = api_client.post("/requirements", json=_api_payload())
    assert created.status_code == 201
    requirement_id = created.json()["id"]

    payload = _api_payload()
    payload["monthly_demand"] = 2200
    payload["change_note"] = "Demand updated after review"
    updated = api_client.put(f"/requirements/{requirement_id}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["current_version"] == 2

    history = api_client.get(f"/requirements/{requirement_id}/versions")
    assert history.status_code == 200
    assert [item["version_number"] for item in history.json()] == [2, 1]
    assert history.json()[0]["snapshot"]["monthly_demand"] == 2200


def test_api_rejects_invalid_requirement_update(api_client):
    created = api_client.post("/requirements", json=_api_payload())
    requirement_id = created.json()["id"]
    payload = _api_payload()
    payload["monthly_demand"] = 0
    payload["change_note"] = "Invalid demand test"
    assert api_client.put(f"/requirements/{requirement_id}", json=payload).status_code == 422


def test_api_missing_requirement_update_and_history_return_404(api_client):
    payload = _api_payload()
    payload["change_note"] = "Missing record test"
    assert api_client.put("/requirements/999", json=payload).status_code == 404
    assert api_client.get("/requirements/999/versions").status_code == 404