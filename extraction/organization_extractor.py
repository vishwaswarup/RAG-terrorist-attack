"""
Organization Extractor
======================

Extracts responsible groups (perpetrators) and target organisations (victims) from text.

Strategy:
    1. spaCy NER — find all ORG entities.
    2. Known groups lists — match against curated lists of
       known militant organisations and security forces.
    3. Context patterns — use linguistic indicators to classify
       groups as perpetrators or targets.
    4. Venue/place filter — remove false positives.
    5. City-name filter — remove geographic names misclassified as orgs.
    6. Parent/child deduplication — prefer specific faction over parent group.
"""

import re
import os
import sys
import spacy

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.regions import CITY_TO_COUNTRY_MAP

# ---------------------------------------------------------------------------
# Load spaCy model
# ---------------------------------------------------------------------------
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Curated lists
# ---------------------------------------------------------------------------
KNOWN_MILITANT_GROUPS = [
    "Islamic State", "ISIS", "ISIL", "Daesh",
    "Islamic State Khorasan Province",
    "Al-Qaeda", "Al Qaeda", "al-Qa'ida",
    "Taliban",
    "Lashkar-e-Taiba", "LeT",
    "Jaish-e-Mohammed", "JeM",
    "Boko Haram",
    "Al-Shabaab", "al Shabaab",
    "Hamas",
    "Hezbollah", "Hizbullah",
    "Hizbul Mujahideen",
    "LTTE", "Tamil Tigers",
    "PKK",
    "ETA",
    "IRA", "Provisional IRA",
    "Tehrik-i-Taliban Pakistan", "TTP",
    "Jamaat-ul-Ahrar",
    "Jundallah",
    "Houthi", "Ansar Allah",
    "Abu Sayyaf",
    "Jemaah Islamiyah",
    "AQAP", "Al-Qaeda in the Arabian Peninsula",
    "AQIM", "Al-Qaeda in the Islamic Maghreb",
    "National Thowheed Jamath", "NTJ",
    "Indian Mujahideen",
    "Bangladesh Rifles",
    "Naxalites", "Maoists",
]

# Specific named forces — auto-classify as target if found in text
KNOWN_SECURITY_FORCES_SPECIFIC = [
    "CRPF", "BSF", "ITBP", "CISF",
    "Indian Army", "Indian Navy", "Indian Air Force",
    "Jammu and Kashmir Police", "J&K Police", "Delhi Police",
    "Punjab Police", "Afghan National Police",
    "Pakistan Rangers", "Airport Security Force",
    "NIA", "NDRF",
    "National Directorate of Security",
    "Border Security Force",
]

# Generic terms — only classify as target if in a TARGET context pattern
KNOWN_SECURITY_FORCES_GENERIC = [
    "Police", "Army", "Navy", "Air Force",
    "Security Forces", "Armed Forces",
]

# Combined for backward compatibility
KNOWN_SECURITY_FORCES = KNOWN_SECURITY_FORCES_SPECIFIC + KNOWN_SECURITY_FORCES_GENERIC

# Parent → child faction mappings.  If both are found, keep only child.
PARENT_CHILD_GROUPS = {
    "Tehrik-i-Taliban Pakistan": ["Jamaat-ul-Ahrar", "Jundallah"],
}

# Known humanitarian / non-combatant organisations that should never be
# classified as perpetrators.
KNOWN_HUMANITARIAN_ORGS = [
    "Medecins Sans Frontieres", "MSF", "Doctors Without Borders",
    "Red Cross", "Red Crescent", "ICRC",
    "United Nations", "UNICEF", "UNHCR", "WHO",
]

# ---------------------------------------------------------------------------
# Venue / Place filter
# ---------------------------------------------------------------------------
VENUE_KEYWORDS = [
    "hotel", "church", "temple", "mosque", "shrine", "cathedral",
    "school", "college", "university", "academy",
    "airport", "station", "terminal", "port",
    "hospital", "clinic", "centre", "center",
    "cafe", "bakery", "restaurant", "market",
    "park", "garden", "stadium", "arena",
    "compound", "building", "tower", "plaza",
    "house", "quarter", "gate", "consulate", "embassy",
    "highway", "road",
]

# Words that should never be an organization name
JUNK_WORDS = [
    "local", "some", "many", "armed", "suspected",
    "citizens", "people", "crowds", "civilians",
    "muslims", "hindus", "christians", "buddhists",
    "residents", "spectators", "families", "nationals",
    "others", "including",
]


def _is_venue(name: str) -> bool:
    """Check if a name looks like a venue/place rather than an organization."""
    name_lower = name.lower()
    return any(kw in name_lower for kw in VENUE_KEYWORDS)


def _is_city_name(name: str) -> bool:
    """Check if a name is a known city/location that shouldn't be an org."""
    # Direct match
    if name.lower() in CITY_TO_COUNTRY_MAP:
        return True
    # Check if name contains only a city name (e.g. "Nagrota")
    for word in name.split():
        if word.lower() in CITY_TO_COUNTRY_MAP:
            # Only reject if name is purely geographic (1-2 words)
            if len(name.split()) <= 2:
                return True
    return False


def _looks_like_sentence_fragment(name: str) -> bool:
    """Reject regex captures that look like sentence fragments, not org names."""
    name_lower = name.lower()
    # Starts with lowercase (except known abbreviations)
    if name[0].islower() and len(name) > 4:
        return True
    # Contains common non-org words
    fragment_indicators = [
        "stormed", "attacked", "fired", "siege", "killed",
        "injured", "wounded", "including", "militants",
        "officers and", "three ", "two ", "the bus",
    ]
    return any(ind in name_lower for ind in fragment_indicators)


# ---------------------------------------------------------------------------
# Context patterns
# ---------------------------------------------------------------------------

_ORG_NAME = r"([A-Z][\w\-']+(?:\s+[\w\-']+){0,5}?)(?:\s+(?:in|on|near|at|from|during|who|which|that|and|or)\b|[,.\;]|\s*$)"

PERPETRATOR_PATTERNS = [
    r"([A-Z][\w\s\-']{2,40}?)\s+claimed\s+responsibility",
    r"responsibility\s+was\s+claimed\s+by\s+(?:the\s+)?" + _ORG_NAME,
    r"carried\s+out\s+by\s+(?:the\s+)?" + _ORG_NAME,
    r"perpetrated\s+by\s+(?:the\s+)?" + _ORG_NAME,
    r"attributed\s+to\s+(?:the\s+)?" + _ORG_NAME,
    r"([A-Z][\w\s\-']{2,40}?)\s+(?:has\s+)?taken\s+credit",
    r"linked\s+to\s+(?:the\s+)?" + _ORG_NAME,
    r"blamed\s+on\s+(?:the\s+)?" + _ORG_NAME,
    r"militants\s+from\s+(?:the\s+)?" + _ORG_NAME,
    r"terrorists\s+from\s+(?:the\s+)?" + _ORG_NAME,
    r"insurgents\s+from\s+(?:the\s+)?" + _ORG_NAME,
    r"attack\s+by\s+(?:the\s+)?" + _ORG_NAME,
    r"bombing\s+by\s+(?:the\s+)?" + _ORG_NAME,
    r"affiliated\s+with\s+(?:the\s+)?" + _ORG_NAME,
]

TARGET_PATTERNS = [
    r"([A-Z][\w\s\-']{2,40}?)\s+personnel\s+were\s+(?:killed|injured|wounded)",
    r"convoy\s+of\s+(?:the\s+)?" + _ORG_NAME,
    r"([A-Z][\w\s\-']{2,40}?)\s+(?:soldiers|troops|police|jawans|cadets|officers)",
    r"targeted\s+(?!by\b)(?:the\s+)?" + _ORG_NAME,
    r"victims\s+included\s+(?:the\s+)?" + _ORG_NAME,
]

def extract_organizations(text: str) -> dict:
    """
    Extract responsible groups and target organisations from text.

    Parameters
    ----------
    text : str
        The raw text to analyse.

    Returns
    -------
    dict
        {"responsible_groups": [...], "target_organizations": [...]}
    """

    responsible = []
    targets = []
    
    seen_resp = set()
    seen_targ = set()

    def _is_valid_org(name: str) -> bool:
        """Shared validation for both responsible and target names."""
        if len(name) < 3:
            return False
        if _is_venue(name):
            return False
        if _is_city_name(name):
            return False
        if _looks_like_sentence_fragment(name):
            return False
        if name.lower() in JUNK_WORDS:
            return False
        return True

    def _add_resp(name: str) -> None:
        name = name.strip()
        if name.lower().startswith("the "):
            name = name[4:]
        if not _is_valid_org(name):
            return
        # Don't add humanitarian orgs as perpetrators
        if any(h.lower() in name.lower() or name.lower() in h.lower()
               for h in KNOWN_HUMANITARIAN_ORGS):
            return
        if name and name.lower() not in seen_resp:
            seen_resp.add(name.lower())
            responsible.append(name)

    def _add_targ(name: str) -> None:
        name = name.strip()
        if name.lower().startswith("the "):
            name = name[4:]
        if not _is_valid_org(name):
            return
        if name and name.lower() not in seen_targ:
            seen_targ.add(name.lower())
            targets.append(name)

    text_lower = text.lower()

    # --- 1. Known Lists (Explicit Matches) ---------------------------------
    for group in KNOWN_MILITANT_GROUPS:
        if len(group) <= 4:
            if re.search(r"\b" + re.escape(group) + r"\b", text):
                _add_resp(group)
        else:
            if group.lower() in text_lower:
                _add_resp(group)

    # Only add SPECIFIC security forces automatically as targets
    for force in KNOWN_SECURITY_FORCES_SPECIFIC:
        if len(force) <= 4:
            if re.search(r"\b" + re.escape(force) + r"\b", text):
                _add_targ(force)
        else:
            if force.lower() in text_lower:
                _add_targ(force)

    # Generic forces ("Security Forces", "Army", "Police") are NOT auto-added.
    # They are only added if they match a TARGET context pattern (below).

    # --- 2. Context Patterns -----------------------------------------------
    for pattern in PERPETRATOR_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            _add_resp(match.group(1))

    for pattern in TARGET_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            _add_targ(match.group(1))

    # --- 3. spaCy NER (Fallback classification) ----------------------------
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            name = ent.text.strip()
            if name.lower().startswith("the "):
                name = name[4:]
            name_lower = name.lower()
            
            # If already explicitly classified via lists or patterns, skip
            if name_lower in seen_resp or name_lower in seen_targ:
                continue
                
            # If it overlaps with known security forces (specific), it's a target
            is_security_force = any(
                (f.lower() in name_lower) or (name_lower in f.lower()) 
                for f in KNOWN_SECURITY_FORCES_SPECIFIC
            )
            
            # If it overlaps with known militant groups, it's responsible
            is_militant = any(
                (m.lower() in name_lower) or (name_lower in m.lower())
                for m in KNOWN_MILITANT_GROUPS
            )
            
            if is_security_force:
                _add_targ(name)
            elif is_militant:
                _add_resp(name)
            # Don't add unknown ORGs — too many false positives

    # --- 4. Parent/Child Deduplication ------------------------------------
    # If both a parent group AND its child faction are found,
    # remove the parent (the child is more specific/accurate).
    resp_lower = {r.lower() for r in responsible}
    for parent, children in PARENT_CHILD_GROUPS.items():
        if parent.lower() in resp_lower:
            # Check if any child is also present
            if any(child.lower() in resp_lower for child in children):
                # Remove the parent
                responsible = [r for r in responsible if r.lower() != parent.lower()]

    # --- 5. Substring Deduplication ----------------------------------------
    def deduplicate(items, known_set):
        items = sorted(list(set(items)), key=len, reverse=True)
        final = []
        for item in items:
            item_lower = item.lower()
            contains_known = any(k.lower() in item_lower and k.lower() != item_lower for k in known_set)
            is_known = any(item_lower == k.lower() for k in known_set)
            
            if contains_known and not is_known:
                continue
                
            if any(item_lower in f.lower() for f in final):
                continue
                
            final.append(item)
        return final

    known_militants_set = set(KNOWN_MILITANT_GROUPS)
    known_forces_set = set(KNOWN_SECURITY_FORCES)

    responsible = deduplicate(responsible, known_militants_set)
    targets = deduplicate(targets, known_forces_set)

    return {
        "responsible_groups": responsible,
        "target_organizations": targets
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "Jaish-e-Mohammed claimed responsibility for the attack. 40 CRPF personnel were killed.",
        "ISIS claimed responsibility. Local police confirmed the casualties.",
        "The convoy of the Indian Army was targeted by Lashkar-e-Taiba militants."
    ]

    for s in samples:
        result = extract_organizations(s)
        print(f"Text: {s}")
        print(f"  Responsible: {result['responsible_groups']}")
        print(f"  Targets    : {result['target_organizations']}")
        print()
