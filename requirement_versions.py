"""Versioned editing for LineFlex production requirements.

Each saved edit creates a complete JSON snapshot. Historical snapshots are
records of what the user entered, not a verification of manufacturing data.
"""

import json
import sqlite3
from pathlib import Path

from database import DEFAULT_DB
from planning import (
    _clean_required_capabilities,
    _clean_requirement_fields,
    get_production_requirement,
    initialize_planning_tables,
)


def _connect(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _snapshot_from_connection(conn, requirement_id):
    row = conn.execute(
        "SELECT * FROM production_requirements WHERE id = ?", (requirement_id,)
    ).fetchone()
    if row is None:
        return None

    snapshot = {
        "requirement_name": row["requirement_name"],
        "part_number": row["part_number"],
        "monthly_demand": row["monthly_demand"],
        "capacity_unit": row["capacity_unit"],
        "notes": row["notes"],
        "required_capabilities": {
            "Machine": [], "Process": [], "Material": [], "Certification": []
        },
    }
    items = conn.execute(
        """SELECT category, value FROM production_requirement_items
           WHERE requirement_id = ? ORDER BY category, value""",
        (requirement_id,),
    ).fetchall()
    for item in items:
        snapshot["required_capabilities"].setdefault(item["category"], []).append(item["value"])
    return snapshot


def initialize_requirement_version_tables(db_path=DEFAULT_DB):
    """Create version storage and add a v1 snapshot for existing requirements."""
    initialize_planning_tables(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS production_requirement_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL,
                change_note TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(requirement_id) REFERENCES production_requirements(id)
                    ON DELETE CASCADE,
                UNIQUE(requirement_id, version_number)
            )"""
        )
        existing_ids = conn.execute(
            """SELECT r.id FROM production_requirements r
               WHERE NOT EXISTS (
                   SELECT 1 FROM production_requirement_versions v
                   WHERE v.requirement_id = r.id
               ) ORDER BY r.id"""
        ).fetchall()
        for row in existing_ids:
            requirement_id = row["id"]
            snapshot = _snapshot_from_connection(conn, requirement_id)
            if snapshot is not None:
                conn.execute(
                    """INSERT INTO production_requirement_versions
                       (requirement_id, version_number, snapshot_json, change_note)
                       VALUES (?, 1, ?, ?)""",
                    (requirement_id, json.dumps(snapshot, sort_keys=True), "Initial version"),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_requirement_version_history(requirement_id, db_path=DEFAULT_DB):
    """Return immutable snapshots, newest version first."""
    initialize_requirement_version_tables(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT version_number, snapshot_json, change_note, changed_at
               FROM production_requirement_versions
               WHERE requirement_id = ? ORDER BY version_number DESC""",
            (requirement_id,),
        ).fetchall()
        history = []
        for row in rows:
            item = dict(row)
            item["snapshot"] = json.loads(item.pop("snapshot_json"))
            history.append(item)
        return history
    finally:
        conn.close()


def update_production_requirement(
    requirement_id,
    requirement_name,
    monthly_demand,
    capacity_unit,
    part_number="",
    notes="",
    required_capabilities=None,
    change_note="",
    db_path=DEFAULT_DB,
):
    """Update a requirement and append a full snapshot as the next version."""
    fields = _clean_requirement_fields(
        requirement_name, part_number, monthly_demand, capacity_unit, notes
    )
    capabilities = _clean_required_capabilities(required_capabilities)
    change_note = str(change_note or "").strip()
    if not change_note:
        raise ValueError("A change note is required to save a new version.")
    if len(change_note) > 300:
        raise ValueError("Change note must be 300 characters or fewer.")

    initialize_requirement_version_tables(db_path)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        exists = conn.execute(
            "SELECT id FROM production_requirements WHERE id = ?", (requirement_id,)
        ).fetchone()
        if exists is None:
            conn.rollback()
            return None

        latest = conn.execute(
            """SELECT COALESCE(MAX(version_number), 0) AS latest
               FROM production_requirement_versions WHERE requirement_id = ?""",
            (requirement_id,),
        ).fetchone()["latest"]
        next_version = int(latest) + 1

        conn.execute(
            """UPDATE production_requirements
               SET requirement_name = ?, part_number = ?, monthly_demand = ?,
                   capacity_unit = ?, notes = ?
               WHERE id = ?""",
            (*fields, requirement_id),
        )
        conn.execute(
            "DELETE FROM production_requirement_items WHERE requirement_id = ?",
            (requirement_id,),
        )
        for category, values in capabilities.items():
            conn.executemany(
                """INSERT INTO production_requirement_items
                   (requirement_id, category, value) VALUES (?, ?, ?)""",
                [(requirement_id, category, value) for value in values],
            )

        snapshot = _snapshot_from_connection(conn, requirement_id)
        conn.execute(
            """INSERT INTO production_requirement_versions
               (requirement_id, version_number, snapshot_json, change_note)
               VALUES (?, ?, ?, ?)""",
            (requirement_id, next_version, json.dumps(snapshot, sort_keys=True), change_note),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    updated = get_production_requirement(requirement_id, db_path=db_path)
    if updated is not None:
        updated["current_version"] = next_version
    return updated