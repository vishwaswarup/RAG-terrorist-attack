"""
Incident Repository
===================

CRUD operations for persisting Incident objects to SQLite.

List fields (attack_types, target_types, weapon_types,
responsible_groups, target_organizations) are stored as
comma-separated strings.
"""

import os
import sys

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident
from storage.database import get_connection, initialize_database


def _list_to_csv(items: list[str]) -> str:
    """Convert a Python list of strings to a comma-separated string."""
    return ",".join(items) if items else ""


def _csv_to_list(csv_str: str) -> list[str]:
    """Convert a comma-separated string back to a Python list."""
    if not csv_str:
        return []
    return [s.strip() for s in csv_str.split(",") if s.strip()]


def save_incident(incident: Incident) -> None:
    """
    Insert or replace an incident in the database.

    Parameters
    ----------
    incident : Incident
        The incident object to persist.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO incidents (
                incident_id,
                date,
                country, state, city,
                location_confidence,
                attack_types, target_types, weapon_types,
                responsible_groups, target_organizations,
                killed, injured,
                summary,
                source_document_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident.incident_id,
                incident.date,
                incident.country,
                incident.state,
                incident.city,
                incident.location_confidence,
                _list_to_csv(incident.attack_types),
                _list_to_csv(incident.target_types),
                _list_to_csv(incident.weapon_types),
                _list_to_csv(incident.responsible_groups),
                _list_to_csv(incident.target_organizations),
                incident.killed,
                incident.injured,
                incident.summary,
                incident.source_document_id,
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"  DATABASE ERROR: {e}")
    finally:
        conn.close()


def get_incident(incident_id: str) -> Incident | None:
    """
    Retrieve a single incident by its ID.

    Parameters
    ----------
    incident_id : str
        The UUID of the incident to retrieve.

    Returns
    -------
    Incident or None
        The incident object, or None if not found.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?",
            (incident_id,),
        ).fetchone()

        if row is None:
            return None

        return Incident(
            incident_id=row["incident_id"],
            date=row["date"] or "",
            country=row["country"] or "",
            state=row["state"] or "",
            city=row["city"] or "",
            location_confidence=row["location_confidence"] or 0.0,
            attack_types=_csv_to_list(row["attack_types"]),
            target_types=_csv_to_list(row["target_types"]),
            weapon_types=_csv_to_list(row["weapon_types"]),
            responsible_groups=_csv_to_list(row["responsible_groups"]),
            target_organizations=_csv_to_list(row["target_organizations"]),
            killed=row["killed"] or 0,
            injured=row["injured"] or 0,
            summary=row["summary"] or "",
            source_document_id=row["source_document_id"] or "",
        )
    except Exception as e:
        print(f"  DATABASE ERROR: {e}")
        return None
    finally:
        conn.close()


def get_all_incidents() -> list[Incident]:
    """
    Retrieve all incidents from the database.

    Returns
    -------
    list[Incident]
        All stored incidents.
    """
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM incidents").fetchall()

        incidents = []
        for row in rows:
            incidents.append(
                Incident(
                    incident_id=row["incident_id"],
                    date=row["date"] or "",
                    country=row["country"] or "",
                    state=row["state"] or "",
                    city=row["city"] or "",
                    location_confidence=row["location_confidence"] or 0.0,
                    attack_types=_csv_to_list(row["attack_types"]),
                    target_types=_csv_to_list(row["target_types"]),
                    weapon_types=_csv_to_list(row["weapon_types"]),
                    responsible_groups=_csv_to_list(row["responsible_groups"]),
                    target_organizations=_csv_to_list(row["target_organizations"]),
                    killed=row["killed"] or 0,
                    injured=row["injured"] or 0,
                    summary=row["summary"] or "",
                    source_document_id=row["source_document_id"] or "",
                )
            )
        return incidents
    except Exception as e:
        print(f"  DATABASE ERROR: {e}")
        return []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    initialize_database()

    # Fetch and print all stored incidents
    incidents = get_all_incidents()
    print(f"\n  Total incidents in DB: {len(incidents)}")
    for inc in incidents:
        print(f"    {inc.incident_id} | {inc.date} | {inc.country} | {inc.city}")
