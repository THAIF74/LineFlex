"""Production requirement records and transparent capability comparisons.

Comparisons use exact, case-insensitive labels and factory-entered stated capacity.
They are screening aids only, not engineering or supplier approval decisions.
"""

import math
import sqlite3
from pathlib import Path

from database import CAPABILITY_CATEGORIES, DEFAULT_DB, get_factories


PLANNING_CATEGORIES = CAPABILITY_CATEGORIES
COMPARISON_LIMITATION = (
    "This comparison uses exact capability labels and user-entered stated monthly "
    "capacity only. It does not verify free capacity, technical equivalence, quality, "
    "certification validity, delivery performance, or customer approval."
)


def _connection(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_planning_tables(db_path=DEFAULT_DB):
    """Create planning tables while preserving existing factory data."""
    from database import initialize_db

    initialize_db(db_path)
    conn = _connection(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS production_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_name TEXT NOT NULL,
                part_number TEXT NOT NULL DEFAULT '',
                monthly_demand REAL NOT NULL CHECK(monthly_demand > 0),
                capacity_unit TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS production_requirement_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('Machine', 'Process', 'Material', 'Certification')),
                value TEXT NOT NULL,
                FOREIGN KEY(requirement_id) REFERENCES production_requirements(id)
                    ON DELETE CASCADE,
                UNIQUE(requirement_id, category, value)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _clean_requirement_fields(requirement_name, part_number, monthly_demand, capacity_unit, notes):
    name = str(requirement_name or "").strip()
    part = str(part_number or "").strip()
    unit = str(capacity_unit or "").strip()
    note_text = str(notes or "").strip()
    if not name:
        raise ValueError("Requirement name is required.")
    if len(name) > 150:
        raise ValueError("Requirement name must be 150 characters or fewer.")
    if len(part) > 100:
        raise ValueError("Part number must be 100 characters or fewer.")
    if not unit:
        raise ValueError("Capacity unit is required.")
    if len(unit) > 40:
        raise ValueError("Capacity unit must be 40 characters or fewer.")
    if len(note_text) > 1000:
        raise ValueError("Notes must be 1000 characters or fewer.")
    try:
        demand = float(monthly_demand)
    except (TypeError, ValueError) as exc:
        raise ValueError("Monthly demand must be a valid number.") from exc
    if not math.isfinite(demand) or demand <= 0:
        raise ValueError("Monthly demand must be a finite number greater than zero.")
    return name, part, demand, unit, note_text


def _clean_required_capabilities(required_capabilities):
    if required_capabilities is None:
        required_capabilities = {}
    if not isinstance(required_capabilities, dict):
        raise ValueError("Required capabilities must be an object grouped by category.")
    unknown = set(required_capabilities) - set(PLANNING_CATEGORIES)
    if unknown:
        raise ValueError("Unknown capability categories: " + ", ".join(sorted(unknown)))

    cleaned = {}
    for category in PLANNING_CATEGORIES:
        values = required_capabilities.get(category, [])
        if values is None:
            values = []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            raise ValueError(f"{category} requirements must be a list of text values.")
        seen = set()
        output = []
        for item in values:
            value = str(item).strip()
            if value and value.casefold() not in seen:
                output.append(value)
                seen.add(value.casefold())
        cleaned[category] = output
    return cleaned


def add_production_requirement(
    requirement_name,
    monthly_demand,
    capacity_unit,
    part_number="",
    notes="",
    required_capabilities=None,
    db_path=DEFAULT_DB,
):
    fields = _clean_requirement_fields(
        requirement_name, part_number, monthly_demand, capacity_unit, notes
    )
    capabilities = _clean_required_capabilities(required_capabilities)
    initialize_planning_tables(db_path)
    conn = _connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO production_requirements
               (requirement_name, part_number, monthly_demand, capacity_unit, notes)
               VALUES (?, ?, ?, ?, ?)""",
            fields,
        )
        requirement_id = cursor.lastrowid
        for category, values in capabilities.items():
            conn.executemany(
                """INSERT INTO production_requirement_items
                   (requirement_id, category, value) VALUES (?, ?, ?)""",
                [(requirement_id, category, value) for value in values],
            )
        conn.commit()
        return requirement_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _requirement_from_row(conn, row):
    if row is None:
        return None
    requirement = dict(row)
    requirement["required_capabilities"] = {category: [] for category in PLANNING_CATEGORIES}
    items = conn.execute(
        """SELECT category, value FROM production_requirement_items
           WHERE requirement_id = ? ORDER BY category, value""",
        (requirement["id"],),
    ).fetchall()
    for item in items:
        requirement["required_capabilities"].setdefault(item["category"], []).append(item["value"])
    return requirement


def get_production_requirement(requirement_id, db_path=DEFAULT_DB):
    initialize_planning_tables(db_path)
    conn = _connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM production_requirements WHERE id = ?", (requirement_id,)
        ).fetchone()
        return _requirement_from_row(conn, row)
    finally:
        conn.close()


def get_production_requirements(search="", db_path=DEFAULT_DB):
    initialize_planning_tables(db_path)
    term = str(search or "").strip()
    pattern = f"%{term}%"
    conn = _connection(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM production_requirements
               WHERE requirement_name LIKE ? OR part_number LIKE ?
               ORDER BY created_at DESC, id DESC""",
            (pattern, pattern),
        ).fetchall()
        return [_requirement_from_row(conn, row) for row in rows]
    finally:
        conn.close()


def delete_production_requirement(requirement_id, db_path=DEFAULT_DB):
    initialize_planning_tables(db_path)
    conn = _connection(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM production_requirements WHERE id = ?", (requirement_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def compare_requirement_to_factories(requirement_id, db_path=DEFAULT_DB):
    """Compare requested labels and demand with each factory's recorded details.

    Status meanings:
      potential_match: all requested labels are present and stated capacity is enough
      needs_more_data: a required capability category has no recorded factory values
      capability_gap: one or more requested labels are absent from recorded values
      below_stated_capacity: stated monthly capacity is below the requirement
      capacity_unit_mismatch: factory and requirement use different units
    """
    requirement = get_production_requirement(requirement_id, db_path=db_path)
    if requirement is None:
        return None

    factories = get_factories(db_path=db_path)
    results = []
    required = requirement["required_capabilities"]

    for factory in factories:
        category_results = {}
        missing_category_data = False
        capability_gap = False

        for category in PLANNING_CATEGORIES:
            requested = required.get(category, [])
            recorded = factory.get("capabilities", {}).get(category, [])
            recorded_lookup = {value.casefold() for value in recorded}
            matched = [value for value in requested if value.casefold() in recorded_lookup]
            missing = [value for value in requested if value.casefold() not in recorded_lookup]

            if not requested:
                category_status = "not_required"
            elif not recorded:
                category_status = "not_recorded"
                missing_category_data = True
            elif not missing:
                category_status = "match"
            elif matched:
                category_status = "partial"
                capability_gap = True
            else:
                category_status = "no_match"
                capability_gap = True

            category_results[category] = {
                "status": category_status,
                "required": requested,
                "matched": matched,
                "missing": missing,
                "factory_recorded": recorded,
            }

        unit_matches = factory["capacity_unit"].strip().casefold() == requirement["capacity_unit"].strip().casefold()
        if not unit_matches:
            capacity_status = "capacity_unit_mismatch"
        elif float(factory["monthly_capacity"]) >= float(requirement["monthly_demand"]):
            capacity_status = "meets_stated_capacity"
        else:
            capacity_status = "below_stated_capacity"

        if capacity_status == "capacity_unit_mismatch":
            overall_status = "capacity_unit_mismatch"
        elif capacity_status == "below_stated_capacity":
            overall_status = "below_stated_capacity"
        elif missing_category_data:
            overall_status = "needs_more_data"
        elif capability_gap:
            overall_status = "capability_gap"
        else:
            overall_status = "potential_match"

        results.append({
            "factory_id": factory["id"],
            "factory_name": factory["factory_name"],
            "city": factory["city"],
            "state": factory["state"],
            "stated_monthly_capacity": factory["monthly_capacity"],
            "factory_capacity_unit": factory["capacity_unit"],
            "required_monthly_demand": requirement["monthly_demand"],
            "required_capacity_unit": requirement["capacity_unit"],
            "capacity_status": capacity_status,
            "capability_results": category_results,
            "overall_status": overall_status,
            "limitation": COMPARISON_LIMITATION,
        })

    results.sort(key=lambda item: (
        {"potential_match": 0, "needs_more_data": 1, "capability_gap": 2,
         "below_stated_capacity": 3, "capacity_unit_mismatch": 4}.get(item["overall_status"], 5),
        item["factory_name"].casefold(),
    ))

    return {"requirement": requirement, "results": results, "limitation": COMPARISON_LIMITATION}
