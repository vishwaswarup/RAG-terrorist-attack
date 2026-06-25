"""
Incident Deduplicator
=====================

Merges incidents that refer to the same real-world event.

After the Incident Builder produces candidate incidents from clustered
sentences, this module checks for duplicates and merges them.

Merge Criteria (any 2 of these → merge):
    1. Same date (or dates within 1 day)
    2. Same city/location
    3. Same responsible group (any set overlap)
    4. High text similarity between summaries (Jaccard > threshold)

Merge Strategy:
    - Date: earliest non-empty
    - Location: most specific (city > state > country)
    - Casualties: max(killed), max(injured) — avoids double-counting
    - Attack/weapon/target types: union of sets
    - Responsible groups: union of sets
    - Summary: concatenation in document order
"""

import re
from datetime import datetime, timedelta
from typing import Optional

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident, generate_retrieval_text


# ---------------------------------------------------------------------------
# Similarity functions
# ---------------------------------------------------------------------------
JACCARD_THRESHOLD = 0.3  # Word-level Jaccard similarity threshold


def _parse_date(date_str: str) -> Optional[datetime]:
    """Try to parse a date string in ISO format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _dates_match(d1: str, d2: str, max_days: int = 1) -> bool:
    """Check if two date strings are the same or within max_days of each other."""
    if not d1 or not d2:
        return False
    dt1 = _parse_date(d1)
    dt2 = _parse_date(d2)
    if dt1 is None or dt2 is None:
        return False
    return abs((dt1 - dt2).days) <= max_days


def _locations_match(inc1: Incident, inc2: Incident) -> bool:
    """Check if two incidents share the same city."""
    if inc1.city and inc2.city:
        return inc1.city.lower() == inc2.city.lower()
    # Fallback: if no city, check state
    if inc1.state and inc2.state and not inc1.city and not inc2.city:
        return inc1.state.lower() == inc2.state.lower()
    return False


def _groups_overlap(inc1: Incident, inc2: Incident) -> bool:
    """Check if responsible groups share any overlap."""
    if not inc1.responsible_groups or not inc2.responsible_groups:
        return False
    s1 = {g.lower() for g in inc1.responsible_groups}
    s2 = {g.lower() for g in inc2.responsible_groups}
    return bool(s1.intersection(s2))


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Compute word-level Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    # Tokenize to words, lowercased, stripped of punctuation
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)


def _texts_similar(inc1: Incident, inc2: Incident) -> bool:
    """Check if summaries have high Jaccard similarity."""
    return _jaccard_similarity(inc1.summary, inc2.summary) > JACCARD_THRESHOLD


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------
def _should_merge(inc1: Incident, inc2: Incident) -> bool:
    """
    Determine if two incidents should be merged.

    Returns True if at least 2 of the 4 criteria are met:
        1. Same date (within 1 day)
        2. Same city/location
        3. Same responsible group
        4. High text similarity
    """
    criteria_met = 0

    if _dates_match(inc1.date, inc2.date):
        criteria_met += 1
    if _locations_match(inc1, inc2):
        criteria_met += 1
    if _groups_overlap(inc1, inc2):
        criteria_met += 1
    if _texts_similar(inc1, inc2):
        criteria_met += 1

    return criteria_met >= 2


def _merge_incidents(primary: Incident, secondary: Incident) -> Incident:
    """
    Merge secondary into primary, returning a new consolidated Incident.

    Strategy:
        - Date: earliest non-empty
        - Location: most specific (city > state > country)
        - Casualties: max of each
        - Lists: union
        - Summary: concatenation (deduped)
    """
    # Date — pick earliest
    merged_date = primary.date
    if not merged_date:
        merged_date = secondary.date
    elif secondary.date:
        d1 = _parse_date(primary.date)
        d2 = _parse_date(secondary.date)
        if d1 and d2:
            merged_date = min(d1, d2).strftime("%Y-%m-%d")

    # Location — prefer most specific
    merged_city = primary.city or secondary.city
    merged_state = primary.state or secondary.state
    merged_country = primary.country or secondary.country

    # If primary has a city, keep its state/country chain
    if primary.city:
        merged_city = primary.city
        merged_state = primary.state or secondary.state
        merged_country = primary.country or secondary.country
    elif secondary.city:
        merged_city = secondary.city
        merged_state = secondary.state or primary.state
        merged_country = secondary.country or primary.country

    merged_confidence = max(primary.location_confidence, secondary.location_confidence)

    # Casualties — max to avoid double-counting
    merged_killed = max(primary.killed, secondary.killed)
    merged_injured = max(primary.injured, secondary.injured)

    # Lists — union
    merged_attack_types = list(set(primary.attack_types) | set(secondary.attack_types))
    merged_target_types = list(set(primary.target_types) | set(secondary.target_types))
    merged_weapon_types = list(set(primary.weapon_types) | set(secondary.weapon_types))
    merged_resp_groups = list(set(primary.responsible_groups) | set(secondary.responsible_groups))
    merged_target_orgs = list(set(primary.target_organizations) | set(secondary.target_organizations))

    # Summary — concatenate, avoiding exact sentence duplication
    primary_sents = set(primary.summary.split(". "))
    secondary_sents = secondary.summary.split(". ")
    new_sents = [s for s in secondary_sents if s not in primary_sents]
    merged_summary = primary.summary
    if new_sents:
        merged_summary += " " + ". ".join(new_sents)

    merged = Incident(
        incident_id=primary.incident_id,  # keep primary ID
        date=merged_date,
        country=merged_country,
        state=merged_state,
        city=merged_city,
        location_confidence=merged_confidence,
        attack_types=merged_attack_types,
        target_types=merged_target_types,
        weapon_types=merged_weapon_types,
        responsible_groups=merged_resp_groups,
        target_organizations=merged_target_orgs,
        killed=merged_killed,
        injured=merged_injured,
        summary=merged_summary,
        has_summary=True,
        source_document_id=primary.source_document_id,
    )

    merged.retrieval_text = generate_retrieval_text(merged)
    return merged


# ---------------------------------------------------------------------------
# Main deduplication function
# ---------------------------------------------------------------------------
def deduplicate_incidents(incidents: list[Incident]) -> list[Incident]:
    """
    Merge duplicate incidents in a list.

    Uses agglomerative approach: iterates through all incident pairs
    and merges when criteria are met, then repeats until stable.

    Parameters
    ----------
    incidents : list[Incident]
        Candidate incidents (may contain duplicates).

    Returns
    -------
    list[Incident]
        Deduplicated list of incidents.
    """
    if len(incidents) <= 1:
        return incidents

    # Agglomerative merge — repeat until no more merges happen
    merged = True
    result = list(incidents)

    while merged:
        merged = False
        new_result = []
        consumed = set()  # indices that have been merged into another

        for i in range(len(result)):
            if i in consumed:
                continue

            current = result[i]

            for j in range(i + 1, len(result)):
                if j in consumed:
                    continue

                if _should_merge(current, result[j]):
                    current = _merge_incidents(current, result[j])
                    consumed.add(j)
                    merged = True

            new_result.append(current)

        result = new_result

    return result


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example: two incidents from the same attack should merge
    inc1 = Incident(
        incident_id="inc-001",
        date="2018-02-10",
        city="Sunjwan",
        state="Jammu and Kashmir",
        country="India",
        attack_types=["Armed Assault"],
        responsible_groups=["Jaish-e-Mohammed"],
        killed=2,
        summary="Two terrorists were killed in an encounter at Sunjwan army camp.",
        source_document_id="doc-001",
    )

    inc2 = Incident(
        incident_id="inc-002",
        date="2018-02-10",
        city="Sunjwan",
        state="Jammu and Kashmir",
        country="India",
        attack_types=["Armed Assault"],
        weapon_types=["Firearms"],
        responsible_groups=["JeM"],
        killed=0,
        summary="JeM militants infiltrated the Sunjwan army camp in Jammu.",
        source_document_id="doc-001",
    )

    result = deduplicate_incidents([inc1, inc2])
    print(f"Input: 2 incidents → Output: {len(result)} incident(s)")
    for inc in result:
        print(f"  Date: {inc.date}")
        print(f"  City: {inc.city}")
        print(f"  Groups: {inc.responsible_groups}")
        print(f"  Killed: {inc.killed}")
