"""Human-managed candidate shortlist records for LineFlex.

A candidate decision is a preliminary sourcing-screen outcome. It is not a
supplier qualification, certification, or authorization to transfer production.
"""

import sqlite3
from pathlib import Path

from database import DEFAULT_DB, get_factory_by_id
from planning import get_production_requirement, initialize_planning_tables

CANDIDATE_DECISIONS = ("Under review", "On hold", "Selected", "Rejected")
FINAL_CANDIDATE_STATUSES = ("Selected", "Rejected")
INITIAL_CANDIDATE_STATUS = "Shortlisted"


def _connect(db_path=DEFAULT_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_candidate_tables(db_path=DEFAULT_DB):
    """Create candidate and decision tables without changing existing records."""
    initialize_planning_tables(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS requirement_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                factory_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Shortlisted',
                added_by TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(requirement_id) REFERENCES production_requirements(id) ON DELETE CASCADE,
                FOREIGN KEY(factory_id) REFERENCES factories(id) ON DELETE CASCADE,
                UNIQUE(requirement_id, factory_id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS candidate_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                decision_by TEXT NOT NULL,
                rationale TEXT NOT NULL,
                decided_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(candidate_id) REFERENCES requirement_candidates(id) ON DELETE CASCADE
            )"""
        )
        conn.commit()
    finally:
        conn.close()


def create_requirement_candidate(
    requirement_id, factory_id, added_by="", notes="", db_path=DEFAULT_DB
):
    """Add a factory to a requirement's shortlist."""
    added_by = str(added_by or "").strip()
    notes = str(notes or "").strip()
    if len(added_by) > 120:
        raise ValueError("Added-by label must be 120 characters or fewer.")
    if len(notes) > 1000:
        raise ValueError("Candidate notes must be 1000 characters or fewer.")
    if get_production_requirement(requirement_id, db_path=db_path) is None:
        raise ValueError("Production requirement was not found.")
    if get_factory_by_id(factory_id, db_path=db_path) is None:
        raise ValueError("Factory was not found.")

    initialize_candidate_tables(db_path)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO requirement_candidates
               (requirement_id, factory_id, added_by, notes)
               VALUES (?, ?, ?, ?)""",
            (requirement_id, factory_id, added_by, notes),
        )
        candidate_id = cursor.lastrowid
        conn.commit()
        return candidate_id
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise ValueError("This factory is already on the shortlist for this requirement.") from exc
    finally:
        conn.close()


def _candidate_from_row(conn, row):
    if row is None:
        return None
    candidate = dict(row)
    candidate["decisions"] = [
        dict(item)
        for item in conn.execute(
            "SELECT * FROM candidate_decisions WHERE candidate_id = ? ORDER BY id DESC",
            (candidate["id"],),
        ).fetchall()
    ]
    return candidate


def get_candidate(candidate_id, db_path=DEFAULT_DB):
    initialize_candidate_tables(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """SELECT c.*, r.requirement_name, r.part_number, f.factory_name,
                      f.city, f.state, f.monthly_capacity, f.capacity_unit
               FROM requirement_candidates c
               JOIN production_requirements r ON r.id = c.requirement_id
               JOIN factories f ON f.id = c.factory_id
               WHERE c.id = ?""",
            (candidate_id,),
        ).fetchone()
        return _candidate_from_row(conn, row)
    finally:
        conn.close()


def get_requirement_candidates(requirement_id, db_path=DEFAULT_DB):
    initialize_candidate_tables(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT c.*, r.requirement_name, r.part_number, f.factory_name,
                      f.city, f.state, f.monthly_capacity, f.capacity_unit
               FROM requirement_candidates c
               JOIN production_requirements r ON r.id = c.requirement_id
               JOIN factories f ON f.id = c.factory_id
               WHERE c.requirement_id = ?
               ORDER BY c.created_at, c.id""",
            (requirement_id,),
        ).fetchall()
        return [_candidate_from_row(conn, row) for row in rows]
    finally:
        conn.close()


def record_candidate_decision(
    candidate_id, decision, decision_by, rationale, db_path=DEFAULT_DB
):
    """Record a named human shortlist decision and preserve its history."""
    if decision not in CANDIDATE_DECISIONS:
        raise ValueError("Decision must be Under review, On hold, Selected, or Rejected.")
    decision_by = str(decision_by or "").strip()
    rationale = str(rationale or "").strip()
    if not decision_by:
        raise ValueError("Decision maker is required.")
    if not rationale:
        raise ValueError("Decision rationale is required.")
    if len(decision_by) > 120 or len(rationale) > 1000:
        raise ValueError("Decision maker or rationale exceeds the allowed length.")

    initialize_candidate_tables(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT status FROM requirement_candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if row is None:
            return None
        previous_status = row["status"]
        if previous_status in FINAL_CANDIDATE_STATUSES:
            raise ValueError(
                "This candidate has a final shortlist decision and is locked. "
                "Create a new review record if it needs reassessment."
            )
        conn.execute(
            """INSERT INTO candidate_decisions
               (candidate_id, previous_status, new_status, decision_by, rationale)
               VALUES (?, ?, ?, ?, ?)""",
            (candidate_id, previous_status, decision, decision_by, rationale),
        )
        conn.execute(
            """UPDATE requirement_candidates
               SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (decision, candidate_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_candidate(candidate_id, db_path=db_path)


def delete_candidate(candidate_id, db_path=DEFAULT_DB):
    initialize_candidate_tables(db_path)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM requirement_candidates WHERE id = ?", (candidate_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
