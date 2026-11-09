import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "lineflex.db"


def initialize_db(db_path=DEFAULT_DB):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS factories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                monthly_capacity REAL NOT NULL CHECK(monthly_capacity > 0),
                capacity_unit TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY(factory_id) REFERENCES factories(id)
                    ON DELETE CASCADE,
                UNIQUE(factory_id, category, value)
            )
        """)


def add_factory(
    factory_name,
    city,
    state,
    monthly_capacity,
    capacity_unit,
    machines,
    processes,
    materials,
    certifications,
    db_path=DEFAULT_DB,
):
    factory_name = factory_name.strip()
    city = city.strip()
    state = state.strip()

    if not factory_name or not city or not state:
        raise ValueError("Factory name, city and state are required.")

    if monthly_capacity <= 0:
        raise ValueError("Monthly capacity must be greater than zero.")

    if not capacity_unit.strip():
        raise ValueError("Capacity unit is required.")

    initialize_db(db_path)

    capability_groups = {
        "Machine": machines,
        "Process": processes,
        "Material": materials,
        "Certification": certifications,
    }

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO factories
            (factory_name, city, state, monthly_capacity, capacity_unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (factory_name, city, state, monthly_capacity, capacity_unit.strip()),
        )

        factory_id = cursor.lastrowid

        for category, values in capability_groups.items():
            for value in values:
                value = value.strip()
                if value:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO capabilities
                        (factory_id, category, value)
                        VALUES (?, ?, ?)
                        """,
                        (factory_id, category, value),
                    )

    return factory_id


def get_factories(search="", db_path=DEFAULT_DB):
    initialize_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT * FROM factories
            WHERE factory_name LIKE ?
               OR city LIKE ?
               OR state LIKE ?
            ORDER BY factory_name
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        ).fetchall()

        factories = []

        for row in rows:
            factory = dict(row)

            capability_rows = conn.execute(
                """
                SELECT category, value FROM capabilities
                WHERE factory_id = ?
                ORDER BY category, value
                """,
                (factory["id"],),
            ).fetchall()

            factory["capabilities"] = {}

            for capability in capability_rows:
                category = capability["category"]
                factory["capabilities"].setdefault(category, []).append(
                    capability["value"]
                )

            factories.append(factory)

        return factories
