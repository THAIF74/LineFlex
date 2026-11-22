import pytest
from fastapi.testclient import TestClient

import api
from database import add_factory, delete_factory
from planning import add_production_requirement, delete_production_requirement
from qualification import (
    CHECK_STATUSES,
    create_checklist_template,
    create_qualification,
    get_checklist_template,
    delete_qualification,
    get_qualification,
    get_qualifications,
    record_qualification_decision,
    update_checklist_template,
    update_qualification_check,
)


def _setup(db_path):
    factory_id = add_factory(
        factory_name="Alternative Components",
        city="Udupi",
        state="Karnataka",
        monthly_capacity=6000,
        capacity_unit="Units",
        machines=["CNC Lathe"],
        processes=["Turning"],
        materials=["Aluminium"],
        certifications=["ISO 9001"],
        db_path=db_path,
    )
    requirement_id = add_production_requirement(
        requirement_name="Housing Part B",
        part_number="HSG-B-002",
        monthly_demand=2500,
        capacity_unit="Units",
        required_capabilities={"Machine": ["CNC Lathe"], "Process": ["Turning"]},
        db_path=db_path,
    )
    return requirement_id, factory_id


def _complete_all_checks(qualification_id, db_path):
    record = get_qualification(qualification_id, db_path=db_path)
    result = None
    for check in record["checks"]:
        result = update_qualification_check(
            qualification_id,
            check["id"],
            "Passed",
            owner="Quality team",
            due_date="2026-12-01",
            evidence_reference=f"evidence/{check['check_key']}.pdf",
            notes="Reviewed during the pilot workflow.",
            db_path=db_path,
        )
    return result


def test_create_qualification_adds_default_checklist(tmp_path):
    db = tmp_path / "qualification.db"
    requirement_id, factory_id = _setup(db)
    qualification_id = create_qualification(requirement_id, factory_id, db_path=db)
    item = get_qualification(qualification_id, db_path=db)
    assert item["status"] == "In progress"
    assert item["checks_total"] == 7
    assert item["checks_passed"] == 0
    assert item["factory_name"] == "Alternative Components"


def test_duplicate_requirement_factory_pair_is_rejected(tmp_path):
    db = tmp_path / "qualification.db"
    requirement_id, factory_id = _setup(db)
    create_qualification(requirement_id, factory_id, db_path=db)
    with pytest.raises(ValueError, match="already exists"):
        create_qualification(requirement_id, factory_id, db_path=db)


def test_missing_requirement_or_factory_is_rejected(tmp_path):
    db = tmp_path / "qualification.db"
    with pytest.raises(ValueError, match="requirement"):
        create_qualification(999, 999, db_path=db)
    requirement_id, _ = _setup(db)
    with pytest.raises(ValueError, match="Factory"):
        create_qualification(requirement_id, 999, db_path=db)


def test_check_update_saves_owner_date_evidence_and_notes(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    check = get_qualification(qual_id, db_path=db)["checks"][0]
    updated = update_qualification_check(
        qual_id, check["id"], "In progress", owner="Engineering",
        due_date="2026-12-05", evidence_reference="drawings/rev-a.pdf",
        notes="Awaiting drawing review.", db_path=db,
    )
    saved = updated["checks"][0]
    assert saved["owner"] == "Engineering"
    assert saved["due_date"] == "2026-12-05"
    assert saved["evidence_reference"] == "drawings/rev-a.pdf"
    assert saved["notes"] == "Awaiting drawing review."


def test_invalid_check_status_is_rejected(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    check = get_qualification(qual_id, db_path=db)["checks"][0]
    with pytest.raises(ValueError, match="Invalid checklist status"):
        update_qualification_check(qual_id, check["id"], "Verified", db_path=db)


def test_invalid_due_date_is_rejected(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    check = get_qualification(qual_id, db_path=db)["checks"][0]
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        update_qualification_check(qual_id, check["id"], "In progress", due_date="tomorrow", db_path=db)


def test_checklist_becomes_ready_for_review_when_all_items_complete(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    updated = _complete_all_checks(qual_id, db)
    assert updated["status"] == "Ready for review"
    assert updated["checks_passed"] == updated["checks_total"] == 7


def test_gap_prevents_ready_for_review(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    record = get_qualification(qual_id, db_path=db)
    for check in record["checks"]:
        update_qualification_check(qual_id, check["id"], "Passed", db_path=db)
    current = get_qualification(qual_id, db_path=db)
    first = current["checks"][0]
    result = update_qualification_check(qual_id, first["id"], "Gap", db_path=db)
    assert result["status"] == "In progress"


def test_approval_requires_all_checks_passed_or_not_applicable(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    with pytest.raises(ValueError, match="every checklist item"):
        record_qualification_decision(qual_id, "Approved", "Reviewer", "Looks good", db_path=db)


def test_approved_decision_is_recorded_in_history(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    _complete_all_checks(qual_id, db)
    result = record_qualification_decision(
        qual_id, "Approved", "Supplier Quality", "All required checks reviewed.", db_path=db
    )
    assert result["status"] == "Approved"
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["previous_status"] == "Ready for review"
    assert result["decisions"][0]["decision_by"] == "Supplier Quality"


def test_final_decision_locks_checklist(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    _complete_all_checks(qual_id, db)
    record_qualification_decision(qual_id, "Approved", "Reviewer", "Checks passed.", db_path=db)
    check = get_qualification(qual_id, db_path=db)["checks"][0]
    with pytest.raises(ValueError, match="finalised"):
        update_qualification_check(qual_id, check["id"], "Gap", db_path=db)


def test_rejected_decision_requires_and_records_rationale(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    with pytest.raises(ValueError, match="rationale"):
        record_qualification_decision(qual_id, "Rejected", "Reviewer", "", db_path=db)
    result = record_qualification_decision(
        qual_id, "Rejected", "Reviewer", "Process evidence was insufficient.", db_path=db
    )
    assert result["status"] == "Rejected"
    assert result["decisions"][0]["decision_notes"] == "Process evidence was insufficient."


def test_delete_qualification_removes_checklist_and_history(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    record_qualification_decision(qual_id, "On hold", "Reviewer", "Waiting for records.", db_path=db)
    assert delete_qualification(qual_id, db_path=db) is True
    assert get_qualification(qual_id, db_path=db) is None


def test_factory_deletion_cascades_qualification(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    assert delete_factory(factory_id, db_path=db) is True
    assert get_qualification(qual_id, db_path=db) is None


def test_requirement_deletion_cascades_qualification(tmp_path):
    db = tmp_path / "qualification.db"
    req_id, factory_id = _setup(db)
    qual_id = create_qualification(req_id, factory_id, db_path=db)
    assert delete_production_requirement(req_id, db_path=db) is True
    assert get_qualification(qual_id, db_path=db) is None


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "qualification-api.db")
    with TestClient(api.app) as client:
        factory = client.post("/factories", json={
            "factory_name": "Qualification API Factory", "city": "Mysuru",
            "state": "Karnataka", "monthly_capacity": 8000,
            "capacity_unit": "Units", "machines": ["CNC Lathe"],
            "processes": ["Turning"], "materials": ["Aluminium"],
            "certifications": ["ISO 9001"],
        })
        req = client.post("/requirements", json={
            "requirement_name": "API Part Requirement", "part_number": "API-P-10",
            "monthly_demand": 2000, "capacity_unit": "Units", "notes": "API test",
            "required_capabilities": {"Machine": ["CNC Lathe"], "Process": ["Turning"]},
        })
        assert factory.status_code == 201
        assert req.status_code == 201
        client.factory_id = factory.json()["id"]
        client.requirement_id = req.json()["id"]
        yield client


def test_api_create_list_and_retrieve_qualification(api_client):
    created = api_client.post("/qualifications", json={
        "requirement_id": api_client.requirement_id,
        "factory_id": api_client.factory_id,
    })
    assert created.status_code == 201
    qual_id = created.json()["id"]
    assert len(created.json()["checks"]) == 7
    listed = api_client.get("/qualifications")
    assert listed.status_code == 200 and len(listed.json()) == 1
    fetched = api_client.get(f"/qualifications/{qual_id}")
    assert fetched.status_code == 200


def test_api_update_check_and_make_decision(api_client):
    created = api_client.post("/qualifications", json={
        "requirement_id": api_client.requirement_id,
        "factory_id": api_client.factory_id,
    })
    qual_id = created.json()["id"]
    checks = created.json()["checks"]
    for check in checks:
        response = api_client.patch(
            f"/qualifications/{qual_id}/checks/{check['id']}",
            json={"status": "Passed", "owner": "Quality", "due_date": "2026-12-01",
                  "evidence_reference": "evidence/check.pdf", "notes": "Reviewed."},
        )
        assert response.status_code == 200
    ready = api_client.get(f"/qualifications/{qual_id}").json()
    assert ready["status"] == "Ready for review"
    decision = api_client.post(f"/qualifications/{qual_id}/decision", json={
        "decision": "Approved", "decision_by": "Quality Lead",
        "decision_notes": "All checks have supporting evidence references.",
    })
    assert decision.status_code == 200
    assert decision.json()["status"] == "Approved"
    history = api_client.get(f"/qualifications/{qual_id}/decisions")
    assert history.status_code == 200 and len(history.json()) == 1


def test_api_rejects_duplicate_candidate(api_client):
    payload = {"requirement_id": api_client.requirement_id, "factory_id": api_client.factory_id}
    assert api_client.post("/qualifications", json=payload).status_code == 201
    assert api_client.post("/qualifications", json=payload).status_code == 409


def test_api_rejects_approval_with_incomplete_checks(api_client):
    created = api_client.post("/qualifications", json={
        "requirement_id": api_client.requirement_id,
        "factory_id": api_client.factory_id,
    })
    qual_id = created.json()["id"]
    response = api_client.post(f"/qualifications/{qual_id}/decision", json={
        "decision": "Approved", "decision_by": "Reviewer", "decision_notes": "Approved prematurely."
    })
    assert response.status_code == 422


def test_api_missing_qualification_returns_404(api_client):
    assert api_client.get("/qualifications/999").status_code == 404



def test_custom_checklist_template_can_be_selected_for_qualification(tmp_path):
    db = tmp_path / "qualification.db"
    requirement_id, factory_id = _setup(db)
    template_id = create_checklist_template(
        name="Aluminium Housing Review",
        description="Review checks for machined aluminium housings.",
        items=[
            ("drawing_review", "Review the latest engineering drawing"),
            ("material_traceability", "Confirm material grade and traceability"),
            ("sample_inspection", "Review sample inspection results"),
        ],
        db_path=db,
    )

    template = get_checklist_template(template_id, db_path=db)
    assert template["name"] == "Aluminium Housing Review"
    assert len(template["items"]) == 3

    qualification_id = create_qualification(
        requirement_id,
        factory_id,
        db_path=db,
        template_id=template_id,
    )
    qualification = get_qualification(qualification_id, db_path=db)
    assert [item["check_key"] for item in qualification["checks"]] == [
        "drawing_review",
        "material_traceability",
        "sample_inspection",
    ]
    assert qualification["checks_total"] == 3


def test_template_edits_do_not_change_existing_qualification_snapshot(tmp_path):
    db = tmp_path / "qualification.db"
    requirement_id, factory_id = _setup(db)
    template_id = create_checklist_template(
        name="Casting Review",
        description="Initial casting review.",
        items=[("visual_review", "Inspect the casting surface")],
        db_path=db,
    )
    qualification_id = create_qualification(
        requirement_id, factory_id, db_path=db, template_id=template_id
    )

    update_checklist_template(
        template_id,
        name="Casting Review Updated",
        description="Updated casting review.",
        items=[
            ("dimensional_review", "Review dimensional inspection"),
            ("material_review", "Confirm material records"),
        ],
        db_path=db,
    )

    saved_qualification = get_qualification(qualification_id, db_path=db)
    saved_template = get_checklist_template(template_id, db_path=db)
    assert [item["title"] for item in saved_qualification["checks"]] == [
        "Inspect the casting surface"
    ]
    assert len(saved_template["items"]) == 2


def test_template_rejects_duplicate_item_keys(tmp_path):
    db = tmp_path / "qualification.db"
    with pytest.raises(ValueError, match="unique"):
        create_checklist_template(
            name="Duplicate Keys",
            description="Invalid template.",
            items=[
                ("drawing_review", "First drawing check"),
                ("DRAWING_REVIEW", "Second drawing check"),
            ],
            db_path=db,
        )


def test_standard_template_cannot_be_deleted(tmp_path):
    db = tmp_path / "qualification.db"
    from qualification import delete_checklist_template, get_checklist_templates

    default_template = next(
        item for item in get_checklist_templates(db_path=db) if item["is_default"]
    )
    with pytest.raises(ValueError, match="cannot be deleted"):
        delete_checklist_template(default_template["id"], db_path=db)


def test_api_can_create_template_and_start_qualification_with_it(api_client):
    created_template = api_client.post(
        "/qualification-templates",
        json={
            "name": "Precision Machining Review",
            "description": "Checks for a precision-machined component.",
            "items": [
                {"check_key": "drawing_review", "title": "Review controlled drawing"},
                {"check_key": "first_article", "title": "Review first-article results"},
            ],
        },
    )
    assert created_template.status_code == 201
    template = created_template.json()
    assert len(template["items"]) == 2

    listed = api_client.get("/qualification-templates")
    assert listed.status_code == 200
    assert any(item["id"] == template["id"] for item in listed.json())

    created_qualification = api_client.post(
        "/qualifications",
        json={
            "requirement_id": api_client.requirement_id,
            "factory_id": api_client.factory_id,
            "template_id": template["id"],
        },
    )
    assert created_qualification.status_code == 201
    assert [
        item["title"] for item in created_qualification.json()["checks"]
    ] == ["Review controlled drawing", "Review first-article results"]
