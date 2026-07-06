"""
GTD Ingestion Script
====================

Parses the raw Global Terrorism Database (GTD) CSV into the standard
Standard Incident schema, generating retrieval text block formatting,
and outputs 4 JSON datasets.
"""

import os
import sys
import csv
import json
import uuid
from dataclasses import asdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident, generate_retrieval_text

def parse_int(val):
    if not val: return 0
    try:
        return int(float(val))
    except ValueError:
        return 0

def format_date(year, month, day):
    y = str(year) if year and str(year) != "0" else "Unknown"
    m = str(month).zfill(2) if month and str(month) != "0" else "01"
    d = str(day).zfill(2) if day and str(day) != "0" else "01"
    
    if y == "Unknown":
        return ""
    return f"{y}-{m}-{d}"

def clean_list(val):
    if not val or val == "Unknown":
        return []
    return [val.strip()]

def main():
    csv_path = os.path.join(PROJECT_ROOT, "storage", "globalterrorismdb_0718dist.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: GTD CSV not found at {csv_path}")
        sys.exit(1)
        
    gtd_full = []
    gtd_summary = []
    gtd_india = []
    gtd_india_summary = []
    
    print("Parsing GTD CSV. This may take a moment...")
    
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = format_date(row.get("iyear"), row.get("imonth"), row.get("iday"))
            summary = row.get("summary", "").strip()
            
            incident = Incident(
                incident_id=str(uuid.uuid4()),
                date=date_str,
                country=row.get("country_txt", ""),
                state=row.get("provstate", ""),
                city=row.get("city", ""),
                attack_types=clean_list(row.get("attacktype1_txt")),
                target_types=clean_list(row.get("targtype1_txt")),
                weapon_types=clean_list(row.get("weaptype1_txt")),
                responsible_groups=clean_list(row.get("gname")),
                killed=parse_int(row.get("nkill")),
                injured=parse_int(row.get("nwound")),
                summary=summary,
                has_summary=bool(summary),
                source_document_id=row.get("eventid", "")
            )
            
            # Generate the standardized block format for FAISS
            incident.retrieval_text = generate_retrieval_text(incident)
            
            # Convert to dict for JSON serialization
            data = asdict(incident)
            
            # Append to lists
            gtd_full.append(data)
            
            if incident.has_summary:
                gtd_summary.append(data)
                
            if incident.country == "India":
                gtd_india.append(data)
                if incident.has_summary:
                    gtd_india_summary.append(data)

    print("\n--- GTD Dataset Generation Complete ---")
    print(f"Total Incidents:             {len(gtd_full):,}")
    print(f"Incidents with summaries:    {len(gtd_summary):,}")
    print(f"Incidents without summaries: {len(gtd_full) - len(gtd_summary):,}")
    pct = (len(gtd_summary) / len(gtd_full)) * 100 if gtd_full else 0
    print(f"Percentage with summaries:   {pct:.1f}%")
    print(f"\nIndia Incidents:             {len(gtd_india):,}")
    print(f"India Incidents w/ summaries:{len(gtd_india_summary):,}")
    
    # Save datasets
    def save_json(data, filename):
        path = os.path.join(PROJECT_ROOT, "storage", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {filename} to storage/")

    save_json(gtd_full, "gtd_full.json")
    save_json(gtd_summary, "gtd_summary.json")
    save_json(gtd_india, "gtd_india.json")
    save_json(gtd_india_summary, "gtd_india_summary.json")

    # Validations against requested metrics
    try:
        assert len(gtd_full) == 181691, f"Expected 181691 total, got {len(gtd_full)}"
        assert len(gtd_summary) == 115562, f"Expected 115562 summaries, got {len(gtd_summary)}"
        assert len(gtd_india) == 11960, f"Expected 11960 India incidents, got {len(gtd_india)}"
        assert len(gtd_india_summary) == 9097, f"Expected 9097 India summaries, got {len(gtd_india_summary)}"
        print("\nAll validation checks PASSED.")
    except AssertionError as e:
        print("\nWARNING: Validation Check Failed!")
        print(e)

if __name__ == "__main__":
    main()
