import pytest
from fastapi.testclient import TestClient

import api
from database import add_factory
from planning import (
    add_production_requirement,
    compare_requirement_to_factories,
    delete_production_requirement,
    get_production_requirement,
    get_production_requirements,
)


def _factory(db_path, **overrides):
    values = {
        "factory_name": "Precision Works",
        "city": "Mangaluru",
        "state": "Karnataka",
        "monthly_capacity": 5000,
        "capacity_unit": "Units",
        "machines": ["CNC Lathe", "VMC"],
        "processes": ["Turning", "Milling"],
        "materials": ["Aluminium", "Steel"],
        "certifications": ["ISO 9001"],
        "db_path": db_path,
    }
    values.update(overrides)
    return add_factory(**values)


def _requirement(db_path, **overrides):
    values = {
        "requirement_name": "Housing Part A",
        "part_number": "HSG-A-001",
        "monthly_demand": 2500,
        "capacity_unit": "Units",
        "notes": "Synthetic test requirement",
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


def test_create_and_retrieve_requirement(tmp_path):
    db = tmp_path / "planning.db"
    requirement_id = _requirement(db)
    record = get_production_requirement(requirement_id, db_path=db)
    assert record["requirement_name"] == "Housing Part A"
    assert record["required_capabilities"]["Machine"] == ["CNC Lathe"]


def test_search_requirements_by_part_number(tmp_path):
    db = tmp_path / "planning.db"
    _requirement(db)
    assert len(get_production_requirements("HSG-A", db_path=db)) == 1


def test_matching_factory_is_potential_match(tmp_path):
    db = tmp_path / "planning.db"
    _factory(db)
    requirement_id = _requirement(db)
    result = compare_requirement_to_factories(requirement_id, db_path=db)
    assert result["results"][0]["overall_status"] == "potential_match"
    assert result["results"][0]["capacity_status"] == "meets_stated_capacity"


def test_unrecorded_required_capability_needs_more_data(tmp_path):
    db = tmp_path / "planning.db"
    _factory(db, certifications=[])
    requirement_id = _requirement(db)
    result = compare_requirement_to_factories(requirement_id, db_path=db)
    assert result["results"][0]["overall_status"] == "needs_more_data"
    assert result["results"][0]["capability_results"]["Certification"]["status"] == "not_recorded"


def test_declared_capability_gap_is_reported(tmp_path):
    db = tmp_path / "planning.db"
    _factory(db, processes=["Milling"])
    requirement_id = _requirement(db)
    result = compare_requirement_to_factories(requirement_id, db_path=db)
    assert result["results"][0]["overall_status"] == "capability_gap"
    assert result["results"][0]["capability_results"]["Process"]["missing"] == ["Turning"]


def test_below_stated_capacity_is_reported(tmp_path):
    db = tmp_path / "planning.db"
    _factory(db, monthly_capacity=1000)
    requirement_id = _requirement(db, monthly_demand=2500)
    result = compare_requirement_to_factories(requirement_id, db_path=db)
    assert result["results"][0]["overall_status"] == "below_stated_capacity"


def test_capacity_unit_mismatch_is_reported(tmp_path):
    db = tmp_path / "planning.db"
    _factory(db, capacity_unit="Tons")
    requirement_id = _requirement(db)
    result = compare_requirement_to_factories(requirement_id, db_path=db)
    assert result["results"][0]["overall_status"] == "capacity_unit_mismatch"


def test_reject_zero_or_non_finite_demand(tmp_path):
    db = tmp_path / "planning.db"
    with pytest.raises(ValueError):
        _requirement(db, monthly_demand=0)
    with pytest.raises(ValueError):
        _requirement(db, monthly_demand=float("inf"))


def test_delete_requirement_cascades_items(tmp_path):
    db = tmp_path / "planning.db"
    requirement_id = _requirement(db)
    assert delete_production_requirement(requirement_id, db_path=db) is True
    assert get_production_requirement(requirement_id, db_path=db) is None


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "api-planning.db")
    with TestClient(api.app) as client:
        yield client


def _api_factory_payload():
    return {
        "factory_name": "API Planning Factory",
        "city": "Mangaluru",
        "state": "Karnataka",
        "monthly_capacity": 5000,
        "capacity_unit": "Units",
        "machines": ["CNC Lathe"],
        "processes": ["Turning"],
        "materials": ["Aluminium"],
        "certifications": ["ISO 9001"],
    }


def _api_requirement_payload():
    return {
        "requirement_name": "API Housing Requirement",
        "part_number": "API-H-01",
        "monthly_demand": 3000,
        "capacity_unit": "Units",
        "notes": "API test requirement",
        "required_capabilities": {
            "Machine": ["CNC Lathe"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
    }


def test_requirement_api_create_list_and_compare(api_client):
    factory = api_client.post("/factories", json=_api_factory_payload())
    assert factory.status_code == 201
    created = api_client.post("/requirements", json=_api_requirement_payload())
    assert created.status_code == 201
    requirement_id = created.json()["id"]
    listed = api_client.get("/requirements?search=API-H-01")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    comparison = api_client.get(f"/requirements/{requirement_id}/matches")
    assert comparison.status_code == 200
    assert comparison.json()["results"][0]["overall_status"] == "potential_match"


def test_requirement_api_rejects_invalid_category(api_client):
    payload = _api_requirement_payload()
    payload["required_capabilities"] = {"Robot": ["Robot X"]}
    response = api_client.post("/requirements", json=payload)
    assert response.status_code == 422


def test_requirement_api_missing_requirement_returns_404(api_client):
    assert api_client.get("/requirements/999/matches").status_code == 404
