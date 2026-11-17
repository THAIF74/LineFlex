"""Second-source qualification tracking for LineFlex.

This module records a human-managed checklist and decision history for a
factory being considered against a production requirement. It is a workflow
tracker, not a certification or technical approval engine.
"""

import sqlite3
from datetime import date
from pathlib import Path

from database import DEFAULT_DB, get_factory_by_id
from planning import get_production_requirement, initialize_planning_tables

CHECK_STATUSES = ("Not started", "In progress", "Passed", "Gap", "Not applicable")
DECISION_STATUSES = ("Approved", "Rejected", "On hold")
FINAL_STATUSES = ("Approved", "Rejected")
COMPLETED_CHECK_STATUSES = ("Passed", "Not applicable")
DEFAULT_CHECKLIST = (
    ("engineering_review", "Engineering drawing and specification review"),
    ("process_review", "Process capability review"),
    ("material_review", "Material and traceability review"),
    ("quality_review", "Quality system and certification review"),
    ("capacity_review", "Capacity and lead-time review"),
    ("sample_review", "Sample or first-article inspection"),
    ("customer_approval", "Customer approval and change-control review"),
)


def _connect(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_qualification_tables(db_path=DEFAULT_DB):
    """Create qualification tables additively; existing registry data is kept."""
    initialize_planning_tables(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS second_source_qualifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                factory_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'In progress',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(requirement_id) REFERENCES production_requirements(id) ON DELETE CASCADE,
                FOREIGN KEY(factory_id) REFERENCES factories(id) ON DELETE CASCADE,
                UNIQUE(requirement_id, factory_id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS qualification_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qualification_id INTEGER NOT NULL,
                check_key TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not started',
                owner TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                evidence_reference TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(qualification_id) REFERENCES second_source_qualifications(id) ON DELETE CASCADE,
                UNIQUE(qualification_id, check_key)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS qualification_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qualification_id INTEGER NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                decision_by TEXT NOT NULL,
                decision_notes TEXT NOT NULL,
                decided_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(qualification_id) REFERENCES second_source_qualifications(id) ON DELETE CASCADE
            )"""
        )
        conn.commit()
    finally:
        conn.close()


def create_qualification(requirement_id, factory_id, db_path=DEFAULT_DB):
    """Start a qualification checklist for one factory/requirement pair."""
    if get_production_requirement(requirement_id, db_path=db_path) is None:
        raise ValueError("Production requirement was not found.")
    if get_factory_by_id(factory_id, db_path=db_path) is None:
        raise ValueError("Factory was not found.")

    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO second_source_qualifications (requirement_id, factory_id)
               VALUES (?, ?)""",
            (requirement_id, factory_id),
        )
        qualification_id = cursor.lastrowid
        conn.executemany(
            """INSERT INTO qualification_checks
               (qualification_id, check_key, title) VALUES (?, ?, ?)""",
            [(qualification_id, key, title) for key, title in DEFAULT_CHECKLIST],
        )
        conn.commit()
        return qualification_id
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise ValueError("A qualification already exists for this factory and requirement.") from exc
    finally:
        conn.close()


def _load_qualification(conn, row):
    if row is None:
        return None
    item = dict(row)
    item["checks"] = [dict(check) for check in conn.execute(
        "SELECT * FROM qualification_checks WHERE qualification_id = ? ORDER BY id",
        (item["id"],),
    ).fetchall()]
    item["decisions"] = [dict(decision) for decision in conn.execute(
        "SELECT * FROM qualification_decisions WHERE qualification_id = ? ORDER BY id",
        (item["id"],),
    ).fetchall()]
    item["checks_passed"] = sum(c["status"] in COMPLETED_CHECK_STATUSES for c in item["checks"])
    item["checks_total"] = len(item["checks"])
    return item


def get_qualification(qualification_id, db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """SELECT q.*, r.requirement_name, r.part_number, f.factory_name,
                      f.city, f.state, f.monthly_capacity, f.capacity_unit
               FROM second_source_qualifications q
               JOIN production_requirements r ON r.id = q.requirement_id
               JOIN factories f ON f.id = q.factory_id
               WHERE q.id = ?""",
            (qualification_id,),
        ).fetchone()
        return _load_qualification(conn, row)
    finally:
        conn.close()


def get_qualifications(requirement_id=None, db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        sql = """SELECT q.*, r.requirement_name, r.part_number, f.factory_name,
                        f.city, f.state, f.monthly_capacity, f.capacity_unit
                 FROM second_source_qualifications q
                 JOIN production_requirements r ON r.id = q.requirement_id
                 JOIN factories f ON f.id = q.factory_id"""
        params = ()
        if requirement_id is not None:
            sql += " WHERE q.requirement_id = ?"
            params = (requirement_id,)
        sql += " ORDER BY q.updated_at DESC, q.id DESC"
        rows = conn.execute(sql, params).fetchall()
        return [_load_qualification(conn, row) for row in rows]
    finally:
        conn.close()


def update_qualification_check(
    qualification_id,
    check_id,
    status,
    owner="",
    due_date="",
    evidence_reference="",
    notes="",
    db_path=DEFAULT_DB,
):
    if status not in CHECK_STATUSES:
        raise ValueError("Invalid checklist status.")
    owner = str(owner or "").strip()
    due_date = str(due_date or "").strip()
    evidence_reference = str(evidence_reference or "").strip()
    notes = str(notes or "").strip()
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError as exc:
            raise ValueError("Due date must use YYYY-MM-DD format.") from exc
    if len(owner) > 120 or len(evidence_reference) > 500 or len(notes) > 1000:
        raise ValueError("Owner, evidence reference, or notes exceed the allowed length.")

    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        parent = conn.execute(
            "SELECT status FROM second_source_qualifications WHERE id = ?", (qualification_id,)
        ).fetchone()
        if parent is None:
            return None
        if parent["status"] in FINAL_STATUSES:
            raise ValueError("A finalised qualification cannot be edited. Start a new qualification if reassessment is needed.")
        cursor = conn.execute(
            """UPDATE qualification_checks SET status = ?, owner = ?, due_date = ?,
               evidence_reference = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND qualification_id = ?""",
            (status, owner, due_date, evidence_reference, notes, check_id, qualification_id),
        )
        if cursor.rowcount == 0:
            return None
        statuses = [row[0] for row in conn.execute(
            "SELECT status FROM qualification_checks WHERE qualification_id = ?",
            (qualification_id,),
        ).fetchall()]
        parent_status = "Ready for review" if statuses and all(
            value in COMPLETED_CHECK_STATUSES for value in statuses
        ) else "In progress"
        conn.execute(
            "UPDATE second_source_qualifications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (parent_status, qualification_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_qualification(qualification_id, db_path=db_path)


def record_qualification_decision(
    qualification_id, decision, decision_by, decision_notes, db_path=DEFAULT_DB
):
    if decision not in DECISION_STATUSES:
        raise ValueError("Decision must be Approved, Rejected, or On hold.")
    decision_by = str(decision_by or "").strip()
    decision_notes = str(decision_notes or "").strip()
    if not decision_by:
        raise ValueError("Decision maker is required.")
    if not decision_notes:
        raise ValueError("Decision rationale is required.")
    if len(decision_by) > 120 or len(decision_notes) > 1000:
        raise ValueError("Decision maker or rationale exceeds the allowed length.")

    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        parent = conn.execute(
            "SELECT status FROM second_source_qualifications WHERE id = ?", (qualification_id,)
        ).fetchone()
        if parent is None:
            return None
        if parent["status"] in FINAL_STATUSES:
            raise ValueError("This qualification already has a final decision and cannot be changed.")
        if decision == "Approved":
            checks = conn.execute(
                "SELECT status FROM qualification_checks WHERE qualification_id = ?",
                (qualification_id,),
            ).fetchall()
            if not checks or any(row["status"] not in COMPLETED_CHECK_STATUSES for row in checks):
                raise ValueError("Approval requires every checklist item to be Passed or Not applicable.")
        previous_status = parent["status"]
        conn.execute(
            """INSERT INTO qualification_decisions
               (qualification_id, previous_status, new_status, decision_by, decision_notes)
               VALUES (?, ?, ?, ?, ?)""",
            (qualification_id, previous_status, decision, decision_by, decision_notes),
        )
        conn.execute(
            "UPDATE second_source_qualifications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (decision, qualification_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_qualification(qualification_id, db_path=db_path)


def delete_qualification(qualification_id, db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM second_source_qualifications WHERE id = ?", (qualification_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
