from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from database import (
    DEFAULT_DB,
    add_factory,
    delete_factory,
    get_factories,
    get_factory_by_id,
    update_factory,
)
from planning import (
    add_production_requirement,
    compare_requirement_to_factories,
    delete_production_requirement,
    get_production_requirement,
    get_production_requirements,
)
from provenance import get_factory_review, save_factory_review

DB_PATH = DEFAULT_DB
app = FastAPI(
    title="LineFlex API",
    description="API for the LineFlex Factory Capability Registry prototype.",
    version="0.3.0",
)


class FactoryPayload(BaseModel):
    factory_name: str = Field(min_length=1, max_length=150)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    monthly_capacity: float = Field(gt=0, allow_inf_nan=False)
    capacity_unit: str = Field(min_length=1, max_length=40)
    machines: list[str] = Field(default_factory=list)
    processes: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    @field_validator("factory_name", "city", "state", "capacity_unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("machines", "processes", "materials", "certifications")
    @classmethod
    def strip_capability_values(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


def _payload_data(payload: FactoryPayload) -> dict:
    return payload.model_dump()


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "LineFlex API"}


@app.post("/factories", status_code=status.HTTP_201_CREATED, tags=["Factories"])
def create_factory(payload: FactoryPayload):
    factory_id = add_factory(**_payload_data(payload), db_path=DB_PATH)
    return get_factory_by_id(factory_id, db_path=DB_PATH)


@app.get("/factories", tags=["Factories"])
def list_factories(search: str = ""):
    return get_factories(search=search, db_path=DB_PATH)


@app.get("/factories/{factory_id}", tags=["Factories"])
def read_factory(factory_id: int):
    factory = get_factory_by_id(factory_id, db_path=DB_PATH)
    if factory is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    return factory


@app.put("/factories/{factory_id}", tags=["Factories"])
def edit_factory(factory_id: int, payload: FactoryPayload):
    updated = update_factory(
        factory_id=factory_id,
        **_payload_data(payload),
        db_path=DB_PATH,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Factory not found")
    return get_factory_by_id(factory_id, db_path=DB_PATH)


@app.delete("/factories/{factory_id}", tags=["Factories"])
def remove_factory(factory_id: int):
    deleted = delete_factory(factory_id, db_path=DB_PATH)
    if not deleted:
        raise HTTPException(status_code=404, detail="Factory not found")
    return {"message": "Factory deleted", "factory_id": factory_id}


class FactoryReviewPayload(BaseModel):
    data_source: str = Field(min_length=1, max_length=120)
    verification_status: Literal[
        "Unverified", "Self-declared", "Evidence attached", "Reviewed"
    ] = "Unverified"
    evidence_reference: str = Field(default="", max_length=500)
    reviewed_by: str = Field(default="", max_length=120)

    @field_validator("data_source")
    @classmethod
    def clean_data_source(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Data source cannot be empty.")
        return value

    @field_validator("evidence_reference", "reviewed_by")
    @classmethod
    def clean_optional_text(cls, value: str) -> str:
        return value.strip()


@app.get("/factories/{factory_id}/review", tags=["Factory Data Review"])
def read_factory_review(factory_id: int):
    review = get_factory_review(factory_id, db_path=DB_PATH)
    if review is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    return review


@app.put("/factories/{factory_id}/review", tags=["Factory Data Review"])
def update_factory_review(factory_id: int, payload: FactoryReviewPayload):
    try:
        review = save_factory_review(
            factory_id=factory_id,
            data_source=payload.data_source,
            verification_status=payload.verification_status,
            evidence_reference=payload.evidence_reference,
            reviewed_by=payload.reviewed_by,
            db_path=DB_PATH,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if review is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    return review


class ProductionRequirementPayload(BaseModel):
    requirement_name: str = Field(min_length=1, max_length=150)
    part_number: str = Field(default="", max_length=100)
    monthly_demand: float = Field(gt=0, allow_inf_nan=False)
    capacity_unit: str = Field(min_length=1, max_length=40)
    notes: str = Field(default="", max_length=1000)
    required_capabilities: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("requirement_name", "capacity_unit")
    @classmethod
    def clean_required_requirement_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("part_number", "notes")
    @classmethod
    def clean_optional_requirement_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("required_capabilities")
    @classmethod
    def validate_required_capability_categories(cls, values: dict[str, list[str]]):
        allowed = {"Machine", "Process", "Material", "Certification"}
        unknown = set(values) - allowed
        if unknown:
            raise ValueError("Unknown capability categories: " + ", ".join(sorted(unknown)))
        cleaned = {}
        for category, entries in values.items():
            seen = set()
            cleaned[category] = []
            for entry in entries:
                label = entry.strip()
                if label and label.casefold() not in seen:
                    cleaned[category].append(label)
                    seen.add(label.casefold())
        return cleaned


@app.post("/requirements", status_code=status.HTTP_201_CREATED, tags=["Production Requirements"])
def create_requirement(payload: ProductionRequirementPayload):
    try:
        requirement_id = add_production_requirement(
            requirement_name=payload.requirement_name,
            part_number=payload.part_number,
            monthly_demand=payload.monthly_demand,
            capacity_unit=payload.capacity_unit,
            notes=payload.notes,
            required_capabilities=payload.required_capabilities,
            db_path=DB_PATH,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return get_production_requirement(requirement_id, db_path=DB_PATH)


@app.get("/requirements", tags=["Production Requirements"])
def list_requirements(search: str = ""):
    return get_production_requirements(search=search, db_path=DB_PATH)


@app.get("/requirements/{requirement_id}", tags=["Production Requirements"])
def read_requirement(requirement_id: int):
    requirement = get_production_requirement(requirement_id, db_path=DB_PATH)
    if requirement is None:
        raise HTTPException(status_code=404, detail="Production requirement not found")
    return requirement


@app.delete("/requirements/{requirement_id}", tags=["Production Requirements"])
def remove_requirement(requirement_id: int):
    deleted = delete_production_requirement(requirement_id, db_path=DB_PATH)
    if not deleted:
        raise HTTPException(status_code=404, detail="Production requirement not found")
    return {"message": "Production requirement deleted", "requirement_id": requirement_id}


@app.get("/requirements/{requirement_id}/matches", tags=["Capability Matching"])
def match_requirement(requirement_id: int):
    comparison = compare_requirement_to_factories(requirement_id, db_path=DB_PATH)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Production requirement not found")
    return comparison

# Second-source qualification workflow.
from qualification import (
    CHECK_STATUSES,
    DECISION_STATUSES,
    create_qualification,
    delete_qualification,
    get_qualification,
    get_qualifications,
    record_qualification_decision,
    update_qualification_check,
)


class CreateQualificationPayload(BaseModel):
    requirement_id: int = Field(gt=0)
    factory_id: int = Field(gt=0)


class QualificationCheckPayload(BaseModel):
    status: Literal["Not started", "In progress", "Passed", "Gap", "Not applicable"]
    owner: str = Field(default="", max_length=120)
    due_date: str = Field(default="", max_length=10)
    evidence_reference: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=1000)

    @field_validator("owner", "due_date", "evidence_reference", "notes")
    @classmethod
    def clean_qualification_check_text(cls, value: str) -> str:
        return value.strip()


class QualificationDecisionPayload(BaseModel):
    decision: Literal["Approved", "Rejected", "On hold"]
    decision_by: str = Field(min_length=1, max_length=120)
    decision_notes: str = Field(min_length=1, max_length=1000)

    @field_validator("decision_by", "decision_notes")
    @classmethod
    def clean_decision_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Decision maker and rationale cannot be empty.")
        return value


@app.post("/qualifications", status_code=status.HTTP_201_CREATED, tags=["Second-Source Qualification"])
def start_qualification(payload: CreateQualificationPayload):
    try:
        qualification_id = create_qualification(
            requirement_id=payload.requirement_id,
            factory_id=payload.factory_id,
            db_path=DB_PATH,
        )
    except ValueError as error:
        message = str(error)
        code = 409 if "already exists" in message else 404
        raise HTTPException(status_code=code, detail=message) from error
    return get_qualification(qualification_id, db_path=DB_PATH)


@app.get("/qualifications", tags=["Second-Source Qualification"])
def list_qualifications(requirement_id: int | None = None):
    return get_qualifications(requirement_id=requirement_id, db_path=DB_PATH)


@app.get("/qualifications/{qualification_id}", tags=["Second-Source Qualification"])
def read_qualification(qualification_id: int):
    item = get_qualification(qualification_id, db_path=DB_PATH)
    if item is None:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return item


@app.patch("/qualifications/{qualification_id}/checks/{check_id}", tags=["Second-Source Qualification"])
def edit_qualification_check(
    qualification_id: int, check_id: int, payload: QualificationCheckPayload
):
    try:
        item = update_qualification_check(
            qualification_id=qualification_id,
            check_id=check_id,
            status=payload.status,
            owner=payload.owner,
            due_date=payload.due_date,
            evidence_reference=payload.evidence_reference,
            notes=payload.notes,
            db_path=DB_PATH,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if item is None:
        raise HTTPException(status_code=404, detail="Qualification or checklist item not found")
    return item


@app.post("/qualifications/{qualification_id}/decision", tags=["Second-Source Qualification"])
def decide_qualification(qualification_id: int, payload: QualificationDecisionPayload):
    try:
        item = record_qualification_decision(
            qualification_id=qualification_id,
            decision=payload.decision,
            decision_by=payload.decision_by,
            decision_notes=payload.decision_notes,
            db_path=DB_PATH,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if item is None:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return item


@app.get("/qualifications/{qualification_id}/decisions", tags=["Second-Source Qualification"])
def qualification_decision_history(qualification_id: int):
    item = get_qualification(qualification_id, db_path=DB_PATH)
    if item is None:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return item["decisions"]


@app.delete("/qualifications/{qualification_id}", tags=["Second-Source Qualification"])
def remove_qualification(qualification_id: int):
    deleted = delete_qualification(qualification_id, db_path=DB_PATH)
    if not deleted:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return {"message": "Qualification deleted", "qualification_id": qualification_id}
