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

DB_PATH = DEFAULT_DB
app = FastAPI(
    title="LineFlex API",
    description="API for the LineFlex Factory Capability Registry prototype.",
    version="0.1.0",
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
            raise ValueError("This field cannot be empty or whitespace.")
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
