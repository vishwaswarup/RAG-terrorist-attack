"""
Intelligence Query Layer
========================

Provides functions to retrieve and filter incidents from the SQLite database.
Includes a CLI menu for analysts to quickly test queries.
"""

import os
import sys

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from storage.database import get_connection

def _rows_to_dicts(rows):
    return [dict(row) for row in rows]

def get_all_incidents():
    """Returns all incidents in the database."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM incidents").fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_country(country: str):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM incidents WHERE country = ?", (country,)).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_state(state: str):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM incidents WHERE state = ?", (state,)).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_attack_type(attack_type: str):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE attack_types LIKE ?", 
            (f"%{attack_type}%",)
        ).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_group(group: str):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE responsible_groups LIKE ?", 
            (f"%{group}%",)
        ).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_target_org(org: str):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE target_organizations LIKE ?", 
            (f"%{org}%",)
        ).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()

def get_incidents_by_date_range(start_date: str, end_date: str):
    conn = get_connection()
    try:
        # Assumes date is stored in YYYY-MM-DD format
        rows = conn.execute(
            "SELECT * FROM incidents WHERE date >= ? AND date <= ?", 
            (start_date, end_date)
        ).fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()


def print_incidents(incidents):
    if not incidents:
        print("\n  No incidents found matching the criteria.")
        return

    print(f"\n  Found {len(incidents)} incident(s):")
    for inc in incidents:
        print("\n  " + "-" * 60)
        print(f"  Incident ID       : {inc.get('incident_id')}")
        print(f"  Date              : {inc.get('date')}")
        print(f"  Country           : {inc.get('country')}")
        print(f"  State             : {inc.get('state')}")
        print(f"  City              : {inc.get('city')}")
        print(f"  Attack Types      : {inc.get('attack_types')}")
        print(f"  Responsible Groups: {inc.get('responsible_groups')}")
        print(f"  Target Orgs       : {inc.get('target_organizations')}")
        print(f"  Killed            : {inc.get('killed')}")
        print(f"  Injured           : {inc.get('injured')}")
        summary = inc.get('summary', '')
        if summary and len(summary) > 150:
            summary = summary[:150] + "..."
        print(f"  Summary           : {summary}")
    print("  " + "-" * 60)


def cli_menu():
    while True:
        print("\n========================================")
        print("  Intelligence Query Layer — Phase 3")
        print("========================================")
        print("  1. Show all incidents")
        print("  2. Search by country")
        print("  3. Search by state")
        print("  4. Search by attack type")
        print("  5. Search by responsible group")
        print("  6. Search by target organization")
        print("  7. Search by date range")
        print("  8. Exit")
        print("========================================")
        
        try:
            choice = input("  Select an option (1-8): ").strip()
        except EOFError:
            break
            
        if choice == '1':
            incidents = get_all_incidents()
            print_incidents(incidents)
            
        elif choice == '2':
            country = input("  Enter country: ").strip()
            incidents = get_incidents_by_country(country)
            print_incidents(incidents)
            
        elif choice == '3':
            state = input("  Enter state: ").strip()
            incidents = get_incidents_by_state(state)
            print_incidents(incidents)
            
        elif choice == '4':
            attack = input("  Enter attack type (e.g. Bombing): ").strip()
            incidents = get_incidents_by_attack_type(attack)
            print_incidents(incidents)
            
        elif choice == '5':
            group = input("  Enter responsible group: ").strip()
            incidents = get_incidents_by_group(group)
            print_incidents(incidents)
            
        elif choice == '6':
            org = input("  Enter target organization: ").strip()
            incidents = get_incidents_by_target_org(org)
            print_incidents(incidents)
            
        elif choice == '7':
            start = input("  Enter start date (YYYY-MM-DD): ").strip()
            end = input("  Enter end date (YYYY-MM-DD): ").strip()
            incidents = get_incidents_by_date_range(start, end)
            print_incidents(incidents)
            
        elif choice == '8':
            print("  Exiting.")
            break
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    cli_menu()
