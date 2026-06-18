"""
SQLite Database Layer
=====================

Manages the SQLite connection and schema initialization
for the incident persistence layer.

Database file: incidents.db (project root)
"""

import os
import sqlite3

# ---------------------------------------------------------------------------
# Database path — always in project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "incidents.db")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
CREATE_INCIDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS incidents (
    incident_id         TEXT PRIMARY KEY,
    date                TEXT,
    country             TEXT,
    state               TEXT,
    city                TEXT,
    location_confidence REAL,
    attack_types        TEXT,
    target_types        TEXT,
    weapon_types        TEXT,
    responsible_groups  TEXT,
    target_organizations TEXT,
    killed              INTEGER,
    injured             INTEGER,
    summary             TEXT,
    source_document_id  TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.

    Returns
    -------
    sqlite3.Connection
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # enables dict-like access on rows
    return conn


def create_tables() -> None:
    """Create all required tables if they do not already exist."""
    conn = get_connection()
    try:
        conn.execute(CREATE_INCIDENTS_TABLE)
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    """
    Full database initialization.

    Call this once at startup or from the command line to ensure the
    schema is ready.
    """
    create_tables()
    print(f"  Database initialized successfully.")
    print(f"  Path: {DB_PATH}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    initialize_database()
