"""Second-source qualification tracking for LineFlex.

This module records a human-managed checklist and decision history for a
factory being considered against a production requirement. It is a workflow
tracker, not a certification or technical approval engine.
"""

import re
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
            """CREATE TABLE IF NOT EXISTS qualification_checklist_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS qualification_checklist_template_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                check_key TEXT NOT NULL,
                title TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(template_id) REFERENCES qualification_checklist_templates(id) ON DELETE CASCADE,
                UNIQUE(template_id, check_key)
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
        default_template = conn.execute(
            "SELECT id FROM qualification_checklist_templates WHERE is_default = 1"
        ).fetchone()
        if default_template is None:
            cursor = conn.execute(
                """INSERT INTO qualification_checklist_templates
                   (name, description, is_default) VALUES (?, ?, 1)""",
                (
                    "Standard Second-Source",
                    "General review checklist for a second-source manufacturing candidate.",
                ),
            )
            default_template_id = cursor.lastrowid
            conn.executemany(
                """INSERT INTO qualification_checklist_template_items
                   (template_id, check_key, title, sort_order) VALUES (?, ?, ?, ?)""",
                [
                    (default_template_id, key, title, index)
                    for index, (key, title) in enumerate(DEFAULT_CHECKLIST)
                ],
            )
        else:
            item_count = conn.execute(
                "SELECT COUNT(*) FROM qualification_checklist_template_items WHERE template_id = ?",
                (default_template["id"],),
            ).fetchone()[0]
            if item_count == 0:
                conn.executemany(
                    """INSERT INTO qualification_checklist_template_items
                       (template_id, check_key, title, sort_order) VALUES (?, ?, ?, ?)""",
                    [
                        (default_template["id"], key, title, index)
                        for index, (key, title) in enumerate(DEFAULT_CHECKLIST)
                    ],
                )
        conn.commit()
    finally:
        conn.close()


def _clean_checklist_template(name, description, items):
    name = str(name or "").strip()
    description = str(description or "").strip()
    if not name:
        raise ValueError("Template name is required.")
    if len(name) > 120 or len(description) > 500:
        raise ValueError("Template name or description exceeds the allowed length.")
    if not isinstance(items, (list, tuple)) or not items:
        raise ValueError("A checklist template must contain at least one item.")
    if len(items) > 30:
        raise ValueError("A checklist template cannot contain more than 30 items.")

    cleaned = []
    seen = set()
    for item in items:
        if isinstance(item, dict):
            key = item.get("check_key", item.get("key", ""))
            title = item.get("title", "")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            key, title = item
        else:
            raise ValueError("Each checklist item must contain a key and title.")

        key = str(key or "").strip().casefold()
        title = str(title or "").strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,49}", key):
            raise ValueError(
                "Checklist keys must start with a letter and contain only letters, numbers, or underscores."
            )
        if key in seen:
            raise ValueError("Checklist item keys must be unique within a template.")
        if not title or len(title) > 160:
            raise ValueError("Each checklist item needs a title of 1 to 160 characters.")
        seen.add(key)
        cleaned.append((key, title))
    return name, description, cleaned


def _load_checklist_template(conn, row):
    if row is None:
        return None
    template = dict(row)
    template["items"] = [
        dict(item)
        for item in conn.execute(
            """SELECT check_key, title, sort_order
               FROM qualification_checklist_template_items
               WHERE template_id = ? ORDER BY sort_order, id""",
            (template["id"],),
        ).fetchall()
    ]
    return template


def get_checklist_templates(db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM qualification_checklist_templates
               ORDER BY is_default DESC, name COLLATE NOCASE, id"""
        ).fetchall()
        return [_load_checklist_template(conn, row) for row in rows]
    finally:
        conn.close()


def get_checklist_template(template_id, db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM qualification_checklist_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        return _load_checklist_template(conn, row)
    finally:
        conn.close()


def get_default_checklist_template(db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM qualification_checklist_templates WHERE is_default = 1"
        ).fetchone()
        return _load_checklist_template(conn, row)
    finally:
        conn.close()


def create_checklist_template(name, description, items, db_path=DEFAULT_DB):
    name, description, cleaned_items = _clean_checklist_template(
        name, description, items
    )
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO qualification_checklist_templates (name, description)
               VALUES (?, ?)""",
            (name, description),
        )
        template_id = cursor.lastrowid
        conn.executemany(
            """INSERT INTO qualification_checklist_template_items
               (template_id, check_key, title, sort_order) VALUES (?, ?, ?, ?)""",
            [
                (template_id, key, title, index)
                for index, (key, title) in enumerate(cleaned_items)
            ],
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise ValueError("A checklist template with this name already exists.") from exc
    finally:
        conn.close()
    return template_id


def update_checklist_template(template_id, name, description, items, db_path=DEFAULT_DB):
    name, description, cleaned_items = _clean_checklist_template(
        name, description, items
    )
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        existing = conn.execute(
            "SELECT is_default FROM qualification_checklist_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if existing is None:
            return None
        if existing["is_default"]:
            raise ValueError("The standard checklist template cannot be edited.")
        conn.execute(
            """UPDATE qualification_checklist_templates
               SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (name, description, template_id),
        )
        conn.execute(
            "DELETE FROM qualification_checklist_template_items WHERE template_id = ?",
            (template_id,),
        )
        conn.executemany(
            """INSERT INTO qualification_checklist_template_items
               (template_id, check_key, title, sort_order) VALUES (?, ?, ?, ?)""",
            [
                (template_id, key, title, index)
                for index, (key, title) in enumerate(cleaned_items)
            ],
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise ValueError("A checklist template with this name already exists.") from exc
    finally:
        conn.close()
    return get_checklist_template(template_id, db_path=db_path)


def delete_checklist_template(template_id, db_path=DEFAULT_DB):
    initialize_qualification_tables(db_path)
    conn = _connect(db_path)
    try:
        existing = conn.execute(
            "SELECT is_default FROM qualification_checklist_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if existing is None:
            return False
        if existing["is_default"]:
            raise ValueError("The standard checklist template cannot be deleted.")
        cursor = conn.execute(
            "DELETE FROM qualification_checklist_templates WHERE id = ?",
            (template_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_qualification(requirement_id, factory_id, db_path=DEFAULT_DB, template_id=None):
    """Start a qualification using a saved checklist template snapshot."""
    if get_production_requirement(requirement_id, db_path=db_path) is None:
        raise ValueError("Production requirement was not found.")
    if get_factory_by_id(factory_id, db_path=db_path) is None:
        raise ValueError("Factory was not found.")

    initialize_qualification_tables(db_path)
    template = (
        get_checklist_template(template_id, db_path=db_path)
        if template_id is not None
        else get_default_checklist_template(db_path=db_path)
    )
    if template is None:
        raise ValueError("Checklist template was not found.")
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
            [
                (qualification_id, item["check_key"], item["title"])
                for item in template["items"]
            ],
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
