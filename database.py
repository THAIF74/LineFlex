import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "lineflex.db"
CAPABILITY_CATEGORIES = ("Machine", "Process", "Material", "Certification")


@contextmanager
def _connection(db_path=DEFAULT_DB):
    """Open a SQLite connection with foreign-key enforcement enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_db(db_path=DEFAULT_DB):
    """Create the registry tables when they do not already exist."""
    with _connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS factories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                monthly_capacity REAL NOT NULL CHECK(monthly_capacity > 0),
                capacity_unit TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY(factory_id) REFERENCES factories(id)
                    ON DELETE CASCADE,
                UNIQUE(factory_id, category, value)
            )
            """
        )


def _clean_factory_fields(factory_name, city, state, monthly_capacity, capacity_unit):
    factory_name = str(factory_name).strip()
    city = str(city).strip()
    state = str(state).strip()
    capacity_unit = str(capacity_unit).strip()

    if not factory_name or not city or not state:
        raise ValueError("Factory name, city and state are required.")
    if not capacity_unit:
        raise ValueError("Capacity unit is required.")

    try:
        monthly_capacity = float(monthly_capacity)
    except (TypeError, ValueError) as exc:
        raise ValueError("Monthly capacity must be a valid number.") from exc

    if not math.isfinite(monthly_capacity) or monthly_capacity <= 0:
        raise ValueError("Monthly capacity must be a finite number greater than zero.")

    return factory_name, city, state, monthly_capacity, capacity_unit


def _clean_values(values):
    if values is None:
        return []
    if isinstance(values, str):
        values = values.split(",")
    cleaned = []
    seen = set()
    for item in values:
        value = str(item).strip()
        if value and value.casefold() not in seen:
            cleaned.append(value)
            seen.add(value.casefold())
    return cleaned


def _save_capabilities(conn, factory_id, machines, processes, materials, certifications):
    groups = {
        "Machine": _clean_values(machines),
        "Process": _clean_values(processes),
        "Material": _clean_values(materials),
        "Certification": _clean_values(certifications),
    }
    for category, values in groups.items():
        conn.executemany(
            """
            INSERT OR IGNORE INTO capabilities (factory_id, category, value)
            VALUES (?, ?, ?)
            """,
            [(factory_id, category, value) for value in values],
        )


def add_factory(
    factory_name,
    city,
    state,
    monthly_capacity,
    capacity_unit,
    machines=None,
    processes=None,
    materials=None,
    certifications=None,
    db_path=DEFAULT_DB,
):
    fields = _clean_factory_fields(
        factory_name, city, state, monthly_capacity, capacity_unit
    )
    initialize_db(db_path)

    with _connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO factories
                (factory_name, city, state, monthly_capacity, capacity_unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            fields,
        )
        factory_id = cursor.lastrowid
        _save_capabilities(
            conn, factory_id, machines, processes, materials, certifications
        )

    return factory_id


def _factory_from_row(conn, row):
    if row is None:
        return None

    factory = dict(row)
    factory["capabilities"] = {category: [] for category in CAPABILITY_CATEGORIES}
    capability_rows = conn.execute(
        """
        SELECT category, value FROM capabilities
        WHERE factory_id = ?
        ORDER BY category, value
        """,
        (factory["id"],),
    ).fetchall()

    for capability in capability_rows:
        category = capability["category"]
        factory["capabilities"].setdefault(category, []).append(capability["value"])

    return factory


def get_factory_by_id(factory_id, db_path=DEFAULT_DB):
    initialize_db(db_path)
    with _connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM factories WHERE id = ?", (factory_id,)
        ).fetchone()
        return _factory_from_row(conn, row)


def get_factories(search="", db_path=DEFAULT_DB):
    initialize_db(db_path)
    search = str(search or "").strip()
    pattern = f"%{search}%"

    with _connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM factories
            WHERE factory_name LIKE ? OR city LIKE ? OR state LIKE ?
            ORDER BY factory_name, id
            """,
            (pattern, pattern, pattern),
        ).fetchall()
        return [_factory_from_row(conn, row) for row in rows]


def update_factory(
    factory_id,
    factory_name,
    city,
    state,
    monthly_capacity,
    capacity_unit,
    machines=None,
    processes=None,
    materials=None,
    certifications=None,
    db_path=DEFAULT_DB,
):
    fields = _clean_factory_fields(
        factory_name, city, state, monthly_capacity, capacity_unit
    )
    initialize_db(db_path)

    with _connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE factories
            SET factory_name = ?, city = ?, state = ?,
                monthly_capacity = ?, capacity_unit = ?
            WHERE id = ?
            """,
            (*fields, factory_id),
        )
        if cursor.rowcount == 0:
            return False

        conn.execute("DELETE FROM capabilities WHERE factory_id = ?", (factory_id,))
        _save_capabilities(
            conn, factory_id, machines, processes, materials, certifications
        )
        return True


def delete_factory(factory_id, db_path=DEFAULT_DB):
    initialize_db(db_path)
    with _connection(db_path) as conn:
        cursor = conn.execute("DELETE FROM factories WHERE id = ?", (factory_id,))
        return cursor.rowcount > 0
