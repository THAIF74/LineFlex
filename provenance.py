"""Factory-level data provenance and review metadata for LineFlex."""

import sqlite3
from pathlib import Path

from database import DEFAULT_DB, get_factory_by_id

VERIFICATION_STATUSES = (
    "Unverified",
    "Self-declared",
    "Evidence attached",
    "Reviewed",
)
DEFAULT_REVIEW = {
    "data_source": "Factory self-report",
    "verification_status": "Unverified",
    "evidence_reference": "",
    "reviewed_by": "",
    "updated_at": None,
}


def initialize_review_table(db_path=DEFAULT_DB):
    """Create review metadata storage without changing existing registry tables."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS factory_reviews (
                factory_id INTEGER PRIMARY KEY,
                data_source TEXT NOT NULL DEFAULT 'Factory self-report',
                verification_status TEXT NOT NULL DEFAULT 'Unverified',
                evidence_reference TEXT NOT NULL DEFAULT '',
                reviewed_by TEXT NOT NULL DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(factory_id) REFERENCES factories(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_factory_review(factory_id, db_path=DEFAULT_DB):
    """Return review metadata, defaulting to Unverified when no review is saved."""
    if get_factory_by_id(factory_id, db_path=db_path) is None:
        return None

    initialize_review_table(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM factory_reviews WHERE factory_id = ?", (factory_id,)
        ).fetchone()
        if row is None:
            return {"factory_id": factory_id, **DEFAULT_REVIEW}
        return dict(row)
    finally:
        conn.close()


def save_factory_review(
    factory_id,
    data_source,
    verification_status,
    evidence_reference="",
    reviewed_by="",
    db_path=DEFAULT_DB,
):
    """Save user-entered review metadata; this does not verify supplied evidence."""
    if get_factory_by_id(factory_id, db_path=db_path) is None:
        return None

    data_source = str(data_source).strip()
    evidence_reference = str(evidence_reference or "").strip()
    reviewed_by = str(reviewed_by or "").strip()

    if not data_source:
        raise ValueError("Data source cannot be empty.")
    if verification_status not in VERIFICATION_STATUSES:
        raise ValueError(
            "Verification status must be one of: " + ", ".join(VERIFICATION_STATUSES)
        )
    if len(data_source) > 120:
        raise ValueError("Data source must be 120 characters or fewer.")
    if len(evidence_reference) > 500:
        raise ValueError("Evidence reference must be 500 characters or fewer.")
    if len(reviewed_by) > 120:
        raise ValueError("Reviewed by must be 120 characters or fewer.")

    initialize_review_table(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT INTO factory_reviews
                (factory_id, data_source, verification_status,
                 evidence_reference, reviewed_by, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(factory_id) DO UPDATE SET
                data_source = excluded.data_source,
                verification_status = excluded.verification_status,
                evidence_reference = excluded.evidence_reference,
                reviewed_by = excluded.reviewed_by,
                updated_at = CURRENT_TIMESTAMP
            """,
            (factory_id, data_source, verification_status, evidence_reference, reviewed_by),
        )
        conn.commit()
    finally:
        conn.close()

    return get_factory_review(factory_id, db_path=db_path)
