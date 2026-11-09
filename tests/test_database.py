import pytest

from database import add_factory, get_factories


def test_add_and_retrieve_factory(tmp_path):
    db_path = tmp_path / "test.db"

    factory_id = add_factory(
        factory_name="Test Precision Works",
        city="Mangaluru",
        state="Karnataka",
        monthly_capacity=5000,
        capacity_unit="Units",
        machines=["CNC Lathe", "VMC"],
        processes=["Turning", "Milling"],
        materials=["Aluminium", "Steel"],
        certifications=["ISO 9001"],
        db_path=db_path,
    )

    factories = get_factories(db_path=db_path)

    assert len(factories) == 1
    assert factories[0]["id"] == factory_id
    assert factories[0]["factory_name"] == "Test Precision Works"
    assert factories[0]["monthly_capacity"] == 5000
    assert factories[0]["capabilities"]["Machine"] == [
        "CNC Lathe", "VMC"
    ]
    assert factories[0]["capabilities"]["Process"] == [
        "Milling", "Turning"
    ]


def test_search_by_city(tmp_path):
    db_path = tmp_path / "test.db"

    add_factory(
        factory_name="Coastal Components",
        city="Mangaluru",
        state="Karnataka",
        monthly_capacity=2000,
        capacity_unit="Units",
        machines=[],
        processes=[],
        materials=[],
        certifications=[],
        db_path=db_path,
    )

    results = get_factories("Mangaluru", db_path=db_path)

    assert len(results) == 1
    assert results[0]["factory_name"] == "Coastal Components"


def test_reject_empty_factory_name(tmp_path):
    with pytest.raises(ValueError):
        add_factory(
            factory_name=" ",
            city="Mangaluru",
            state="Karnataka",
            monthly_capacity=1000,
            capacity_unit="Units",
            machines=[],
            processes=[],
            materials=[],
            certifications=[],
            db_path=tmp_path / "test.db",
        )


def test_reject_zero_capacity(tmp_path):
    with pytest.raises(ValueError):
        add_factory(
            factory_name="Test Factory",
            city="Mangaluru",
            state="Karnataka",
            monthly_capacity=0,
            capacity_unit="Units",
            machines=[],
            processes=[],
            materials=[],
            certifications=[],
            db_path=tmp_path / "test.db",
        )
