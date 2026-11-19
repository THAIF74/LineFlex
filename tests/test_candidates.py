import pytest
from fastapi.testclient import TestClient

import api
from database import add_factory, delete_factory
from planning import add_production_requirement, delete_production_requirement
from candidate_shortlists import (
    create_requirement_candidate,
    delete_candidate,
    get_candidate,
    get_requirement_candidates,
    record_candidate_decision,
)


def _factory(db_path):
    return add_factory(
        factory_name="Candidate Works",
        city="Mangaluru",
        state="Karnataka",
        monthly_capacity=5000,
        capacity_unit="Units",
        machines=["CNC Lathe"],
        processes=["Turning"],
        materials=["Aluminium"],
        certifications=["ISO 9001"],
        db_path=db_path,
    )


def _requirement(db_path):
    return add_production_requirement(
        requirement_name="Candidate Test Requirement",
        part_number="CAND-001",
        monthly_demand=2500,
        capacity_unit="Units",
        notes="Synthetic candidate test",
        required_capabilities={
            "Machine": ["CNC Lathe"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
        db_path=db_path,
    )


def test_create_and_list_requirement_candidates(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(
        requirement_id, factory_id, added_by="Planner", notes="Initial review", db_path=db
    )
    candidate = get_candidate(candidate_id, db_path=db)
    records = get_requirement_candidates(requirement_id, db_path=db)
    assert candidate["status"] == "Shortlisted"
    assert candidate["added_by"] == "Planner"
    assert candidate["notes"] == "Initial review"
    assert len(records) == 1
    assert records[0]["factory_id"] == factory_id


def test_duplicate_requirement_candidate_is_rejected(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    create_requirement_candidate(requirement_id, factory_id, db_path=db)
    with pytest.raises(ValueError, match="already on the shortlist"):
        create_requirement_candidate(requirement_id, factory_id, db_path=db)


def test_missing_requirement_is_rejected(tmp_path):
    db = tmp_path / "candidates.db"
    factory_id = _factory(db)
    with pytest.raises(ValueError, match="requirement was not found"):
        create_requirement_candidate(999, factory_id, db_path=db)


def test_missing_factory_is_rejected(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    with pytest.raises(ValueError, match="Factory was not found"):
        create_requirement_candidate(requirement_id, 999, db_path=db)


def test_decision_status_and_history_are_recorded(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    record_candidate_decision(candidate_id, "Under review", "Reviewer A", "Checking details", db_path=db)
    record_candidate_decision(candidate_id, "On hold", "Reviewer B", "Waiting for information", db_path=db)
    selected = record_candidate_decision(candidate_id, "Selected", "Reviewer C", "Proceed to qualification", db_path=db)
    assert selected["status"] == "Selected"
    assert [item["new_status"] for item in selected["decisions"]] == ["Selected", "On hold", "Under review"]
    assert selected["decisions"][0]["decision_by"] == "Reviewer C"


def test_final_candidate_decision_locks_further_changes(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    record_candidate_decision(candidate_id, "Rejected", "Reviewer", "Does not meet current need", db_path=db)
    with pytest.raises(ValueError, match="final shortlist decision"):
        record_candidate_decision(candidate_id, "Under review", "Reviewer", "Reopen", db_path=db)


def test_on_hold_candidate_can_return_to_under_review(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    record_candidate_decision(candidate_id, "On hold", "Reviewer", "Waiting for data", db_path=db)
    updated = record_candidate_decision(candidate_id, "Under review", "Reviewer", "Data received", db_path=db)
    assert updated["status"] == "Under review"
    assert len(updated["decisions"]) == 2


def test_delete_candidate_cascades_decision_history(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    record_candidate_decision(candidate_id, "On hold", "Reviewer", "Waiting", db_path=db)
    assert delete_candidate(candidate_id, db_path=db) is True
    assert get_candidate(candidate_id, db_path=db) is None
    assert get_requirement_candidates(requirement_id, db_path=db) == []


def test_requirement_deletion_cascades_candidates(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    assert delete_production_requirement(requirement_id, db_path=db) is True
    assert get_candidate(candidate_id, db_path=db) is None


def test_factory_deletion_cascades_candidates(tmp_path):
    db = tmp_path / "candidates.db"
    requirement_id = _requirement(db)
    factory_id = _factory(db)
    candidate_id = create_requirement_candidate(requirement_id, factory_id, db_path=db)
    assert delete_factory(factory_id, db_path=db) is True
    assert get_candidate(candidate_id, db_path=db) is None


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "api-candidates.db")
    with TestClient(api.app) as client:
        yield client


def _api_factory_payload():
    return {
        "factory_name": "API Candidate Works",
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
        "requirement_name": "API Candidate Requirement",
        "part_number": "API-CAND-01",
        "monthly_demand": 2500,
        "capacity_unit": "Units",
        "notes": "API candidate test",
        "required_capabilities": {
            "Machine": ["CNC Lathe"],
            "Process": ["Turning"],
            "Material": ["Aluminium"],
            "Certification": ["ISO 9001"],
        },
    }


def test_api_create_list_and_record_candidate_decision(api_client):
    factory = api_client.post("/factories", json=_api_factory_payload())
    requirement = api_client.post("/requirements", json=_api_requirement_payload())
    assert factory.status_code == 201
    assert requirement.status_code == 201
    requirement_id = requirement.json()["id"]
    created = api_client.post(
        f"/requirements/{requirement_id}/candidates",
        json={"factory_id": factory.json()["id"], "added_by": "Planner", "notes": "Compare options"},
    )
    assert created.status_code == 201
    candidate_id = created.json()["id"]
    assert api_client.get(f"/requirements/{requirement_id}/candidates").status_code == 200
    decision = api_client.patch(
        f"/candidates/{candidate_id}/decision",
        json={"decision": "Selected", "decision_by": "Reviewer", "rationale": "Proceed to qualification"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "Selected"
    history = api_client.get(f"/candidates/{candidate_id}/decisions")
    assert history.status_code == 200
    assert history.json()[0]["new_status"] == "Selected"


def test_api_rejects_invalid_candidate_decision_and_missing_candidate(api_client):
    factory = api_client.post("/factories", json=_api_factory_payload())
    requirement = api_client.post("/requirements", json=_api_requirement_payload())
    candidate = api_client.post(
        f"/requirements/{requirement.json()['id']}/candidates",
        json={"factory_id": factory.json()["id"]},
    )
    candidate_id = candidate.json()["id"]
    bad = api_client.patch(
        f"/candidates/{candidate_id}/decision",
        json={"decision": "Approved", "decision_by": "Reviewer", "rationale": "Bad status"},
    )
    assert bad.status_code == 422
    assert api_client.get("/candidates/999/decisions").status_code == 404
