"""
Incident Extraction Pipeline — Phase 2
========================================

Converts a Document object into an Incident object by running
all extraction modules in sequence.

Flow
----
    Document
        ↓
    Date Extractor
        ↓
    Location Extractor
        ↓
    Casualty Extractor
        ↓
    Organization Extractor
        ↓
    Attack/Weapon/Target Extractor
        ↓
    Incident Builder
        ↓
    Incident

Usage
-----
    python3 incident_pipeline.py

Then enter a file path when prompted. The file is first ingested
(Phase 1), then the incident is extracted (Phase 2).
"""

import os
import sys
import uuid

# ---------------------------------------------------------------------------
# Ensure project root is on the path
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.document import Document
from models.incident import Incident

from extraction.clustering.multi_incident_builder import build_multi_incidents

# Import the ingestion pipeline so we can go from file → Document → Incident
from pipeline import ingest

# Import storage layer
from storage.database import initialize_database
from storage.incident_repository import save_incident

# Ensure DB schema exists on import
initialize_database()


def process_document(document: Document) -> list[Incident]:
    """
    Extracts multi-incidents from a Document using clustering.
    Saves each extracted Incident to the database.
    """
    incidents = build_multi_incidents(document)
    for incident in incidents:
        save_incident(incident)
    return incidents


def print_incident(incident: Incident) -> None:
    """Print a formatted incident report."""

    print()
    print("=" * 60)
    print("  EXTRACTED INCIDENT")
    print("=" * 60)
    print()
    print(f"  Incident ID       : {incident.incident_id}")
    print(f"  Source Document    : {incident.source_document_id}")
    print()
    print(f"  Date              : {incident.date or '(not found)'}")
    print(f"  Country           : {incident.country or '(not found)'}")
    print(f"  State             : {incident.state or '(not found)'}")
    print(f"  City              : {incident.city or '(not found)'}")
    print(f"  Loc. Confidence   : {incident.location_confidence:.2f}")
    print()
    print(f"  Attack Types      : {incident.attack_types or '(none detected)'}")
    print(f"  Weapon Types      : {incident.weapon_types or '(none detected)'}")
    print(f"  Target Types      : {incident.target_types or '(none detected)'}")
    print()
    print(f"  Responsible Groups: {incident.responsible_groups or '(none detected)'}")
    print(f"  Target Orgs       : {incident.target_organizations or '(none detected)'}")
    print()
    print(f"  Killed            : {incident.killed}")
    print(f"  Injured           : {incident.injured}")
    print()
    print(f"  Summary           : {incident.summary[:200]}")
    if len(incident.summary) > 200:
        print(f"                      ... (truncated)")
    print()
    print(f"  Retrieval Text    : {incident.retrieval_text}")
    print()
    print("=" * 60)
    print()


def main():
    print()
    print("=" * 60)
    print("  DRDO Phase 2 — Incident Extraction Pipeline")
    print("=" * 60)
    print()

    file_path = input("  Enter file path: ").strip()

    # --- Phase 1: Ingest the file ------------------------------------------
    print()
    print(f"  [Phase 1] Ingesting: {file_path}")
    document = ingest(file_path)

    if document is None:
        print("  ⚠  Ingestion failed.")
        return

    print(f"  [Phase 1] Document created: {document.doc_id}")
    print(f"  [Phase 1] Characters: {len(document.raw_text)}")

    # --- Phase 2: Extract incident -----------------------------------------
    print()
    print(f"  [Phase 2] Discovering & Clustering Events...")

    incidents = process_document(document)
    
    print(f"  [Phase 2] Found {len(incidents)} distinct incident(s).")

    for idx, inc in enumerate(incidents, start=1):
        print(f"\n  --- Incident {idx} of {len(incidents)} ---")
        print_incident(inc)


if __name__ == "__main__":
    main()
