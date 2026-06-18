"""
Incident Dataclass — Phase 2
==============================

Represents a single security incident extracted from a Document.

Each field is populated by a dedicated extractor module:

    date_extractor.py       →  date
    location_extractor.py   →  country, state, city
    casualty_extractor.py   →  killed, injured
    organization_extractor  →  responsible_groups
    attack_extractor.py     →  attack_types, weapon_types, target_types

Fields that cannot be extracted are left at their defaults.
"""

from dataclasses import dataclass, field


@dataclass
class Incident:
    """
    A structured representation of a single security incident.

    Fields
    ------
    incident_id : str
        Unique identifier for this incident (UUID).

    date : str
        Date of the incident in ISO format (YYYY-MM-DD).
        Empty string if no date could be extracted.

    country : str
        Country where the incident occurred.

    state : str
        State / province / region within the country.

    city : str
        City or locality where the incident occurred.

    attack_types : list[str]
        Categories of attack, e.g. ["Bombing", "Armed Assault"].
        Drawn from a controlled vocabulary.

    target_types : list[str]
        Categories of target, e.g. ["Religious", "Civilian"].
        Drawn from a controlled vocabulary.

    weapon_types : list[str]
        Categories of weapon used, e.g. ["Explosives", "Firearms"].
        Drawn from a controlled vocabulary.

    responsible_groups : list[str]
        Names of groups/organisations linked to the incident.

    killed : int
        Number of people killed (0 if unknown).

    injured : int
        Number of people injured (0 if unknown).

    summary : str
        A brief textual summary of the incident.
        Currently the first few sentences of the source document.

    retrieval_text : str
        A structured sentence built from extracted fields,
        useful for future search/retrieval.
        Example: "Bombing attack targeting Religious sites in
                  Sri Lanka causing 269 fatalities."

    source_document_id : str
        The doc_id of the Document this incident was extracted from.
    """

    incident_id: str

    # --- Date ---------------------------------------------------------------
    date: str = ""

    # --- Location -----------------------------------------------------------
    country: str = ""
    state: str = ""
    city: str = ""
    location_confidence: float = 0.0

    # --- Classification -----------------------------------------------------
    attack_types: list[str] = field(default_factory=list)
    target_types: list[str] = field(default_factory=list)
    weapon_types: list[str] = field(default_factory=list)

    # --- Entities -----------------------------------------------------------
    responsible_groups: list[str] = field(default_factory=list)
    target_organizations: list[str] = field(default_factory=list)

    # --- Casualties ---------------------------------------------------------
    killed: int = 0
    injured: int = 0

    # --- Text fields --------------------------------------------------------
    summary: str = ""
    has_summary: bool = False
    retrieval_text: str = ""

    # --- Provenance ---------------------------------------------------------
    source_document_id: str = ""


def generate_retrieval_text(incident: Incident) -> str:
    """
    Generates a standardised key-value block representation of the Incident 
    for FAISS indexing and vector retrieval, ensuring GTD and extracted 
    incidents share the identical embedding format.
    """
    date_str = incident.date if incident.date else "Unknown"
    
    loc_parts = []
    if incident.city: loc_parts.append(incident.city)
    if incident.state: loc_parts.append(incident.state)
    if incident.country: loc_parts.append(incident.country)
    location_str = ", ".join(loc_parts) if loc_parts else "Unknown"

    attack_str = ", ".join(incident.attack_types) if incident.attack_types else "Unknown"
    target_str = ", ".join(incident.target_types) if incident.target_types else "Unknown"
    weapon_str = ", ".join(incident.weapon_types) if incident.weapon_types else "Unknown"
    groups_str = ", ".join(incident.responsible_groups) if incident.responsible_groups else "Unknown"

    base_text = (
        f"Date: {date_str}\n"
        f"Location: {location_str}\n"
        f"Attack Type: {attack_str}\n"
        f"Target Type: {target_str}\n"
        f"Weapon Type: {weapon_str}\n"
        f"Responsible Group: {groups_str}\n"
        f"Killed: {incident.killed}\n"
        f"Injured: {incident.injured}"
    )

    if incident.has_summary and incident.summary.strip():
        base_text += f"\n\nSummary:\n{incident.summary.strip()}"

    return base_text


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = Incident(
        incident_id="inc-demo-001",
        date="2019-04-21",
        country="Sri Lanka",
        city="Colombo",
        attack_types=["Bombing"],
        target_types=["Religious"],
        weapon_types=["Explosives"],
        responsible_groups=["Islamic State"],
        killed=269,
        injured=500,
        summary="A series of coordinated bombings struck churches and hotels.",
        retrieval_text="Bombing attack targeting Religious sites in Sri Lanka causing 269 fatalities.",
        source_document_id="doc-001",
    )

    print("=== Incident Object ===")
    print(f"  ID          : {sample.incident_id}")
    print(f"  Date        : {sample.date}")
    print(f"  Location    : {sample.city}, {sample.state}, {sample.country}")
    print(f"  Attack      : {sample.attack_types}")
    print(f"  Targets     : {sample.target_types}")
    print(f"  Weapons     : {sample.weapon_types}")
    print(f"  Groups      : {sample.responsible_groups}")
    print(f"  Killed      : {sample.killed}")
    print(f"  Injured     : {sample.injured}")
    print(f"  Summary     : {sample.summary}")
    print(f"  Retrieval   : {sample.retrieval_text}")
    print(f"  Source Doc  : {sample.source_document_id}")
