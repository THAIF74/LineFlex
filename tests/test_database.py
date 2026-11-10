import pytest

from database import (
    add_factory,
    delete_factory,
    get_factories,
    get_factory_by_id,
    update_factory,
)


def _factory_data(**overrides):
    data = {
        "factory_name": "Test Precision Works",
        "city": "Mangaluru",
        "state": "Karnataka",
        "monthly_capacity": 5000,
        "capacity_unit": "Units",
        "machines": ["CNC Lathe", "VMC"],
        "processes": ["Turning", "Milling"],
        "materials": ["Aluminium", "Steel"],
        "certifications": ["ISO 9001"],
    }
    data.update(overrides)
    return data


def test_add_and_retrieve_factory(tmp_path):
    db_path = tmp_path / "test.db"
    factory_id = add_factory(**_factory_data(), db_path=db_path)
    factories = get_factories(db_path=db_path)

    assert len(factories) == 1
    assert factories[0]["id"] == factory_id
    assert factories[0]["factory_name"] == "Test Precision Works"
    assert factories[0]["monthly_capacity"] == 5000
    assert factories[0]["capabilities"]["Machine"] == ["CNC Lathe", "VMC"]
    assert factories[0]["capabilities"]["Process"] == ["Milling", "Turning"]


def test_search_by_city(tmp_path):
    db_path = tmp_path / "test.db"
    add_factory(**_factory_data(factory_name="Coastal Components"), db_path=db_path)
    results = get_factories("Mangaluru", db_path=db_path)
    assert len(results) == 1
    assert results[0]["factory_name"] == "Coastal Components"


def test_reject_empty_factory_name(tmp_path):
    with pytest.raises(ValueError):
        add_factory(**_factory_data(factory_name=" "), db_path=tmp_path / "test.db")


def test_reject_zero_capacity(tmp_path):
    with pytest.raises(ValueError):
        add_factory(**_factory_data(monthly_capacity=0), db_path=tmp_path / "test.db")


def test_update_factory_changes_details_and_capabilities(tmp_path):
    db_path = tmp_path / "test.db"
    factory_id = add_factory(**_factory_data(), db_path=db_path)

    updated = update_factory(
        factory_id=factory_id,
        **_factory_data(
            factory_name="Updated Precision Works",
            city="Udupi",
            monthly_capacity=7500,
            machines=["5-axis CNC"],
            processes=["Milling"],
        ),
        db_path=db_path,
    )

    factory = get_factory_by_id(factory_id, db_path=db_path)
    assert updated is True
    assert factory["factory_name"] == "Updated Precision Works"
    assert factory["city"] == "Udupi"
    assert factory["monthly_capacity"] == 7500
    assert factory["capabilities"]["Machine"] == ["5-axis CNC"]
    assert factory["capabilities"]["Process"] == ["Milling"]


def test_delete_factory_also_removes_capabilities(tmp_path):
    db_path = tmp_path / "test.db"
    factory_id = add_factory(**_factory_data(), db_path=db_path)

    assert delete_factory(factory_id, db_path=db_path) is True
    assert get_factory_by_id(factory_id, db_path=db_path) is None
    assert get_factories(db_path=db_path) == []


def test_update_missing_factory_returns_false(tmp_path):
    db_path = tmp_path / "test.db"
    result = update_factory(
        factory_id=999,
        **_factory_data(),
        db_path=db_path,
    )
    assert result is False


def test_reject_infinite_capacity(tmp_path):
    with pytest.raises(ValueError):
        add_factory(
            **_factory_data(monthly_capacity=float("inf")),
            db_path=tmp_path / "test.db",
        )


def test_duplicate_capabilities_are_stored_once(tmp_path):
    db_path = tmp_path / "test.db"
    factory_id = add_factory(
        **_factory_data(machines=["CNC Lathe", "CNC Lathe", " cnc lathe "]),
        db_path=db_path,
    )
    factory = get_factory_by_id(factory_id, db_path=db_path)
    assert factory["capabilities"]["Machine"] == ["CNC Lathe"]
