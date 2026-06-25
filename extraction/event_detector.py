"""
Event Detector
==============

Scores each text chunk on two dimensions — EVENT vs ADMINISTRATIVE —
to determine whether the chunk describes an actual attack/incident
or is investigative/legal/procedural content.

Classification
--------------
    ACCEPT  — chunk describes an actual event; eligible to seed a cluster
    REJECT  — chunk is administrative/legal; excluded from clustering
    NEUTRAL — insufficient signal; can join existing clusters but cannot
              seed new ones

Scoring
-------
    Event Score:
        attack verbs            (+2 each)
        casualty mentions       (+1.5 each)
        weapon mentions         (+1 each)
        attack type mentions    (+1 each)
        target mentions         (+0.5 each)

    Administrative Score:
        investigation terms     (+3 each)
        legal terms             (+3 each)
        accused lists           (+2 each)
        court references        (+1.5 each)
        handler/logistics terms (+2 each)

    Decision:
        admin_score > 0 AND admin_score >= event_score  →  REJECT
        event_score > 0 AND event_score > admin_score   →  ACCEPT
        both 0                                          →  NEUTRAL
"""

import re
from dataclasses import dataclass
from typing import Tuple


# ---------------------------------------------------------------------------
# Positive Event Triggers
# ---------------------------------------------------------------------------
# Core attack verbs — the STRONGEST indicators of an actual incident.
# These receive a bonus in mixed-content sentences.
CORE_ATTACK_VERBS = [
    "encounter", "killed", "attacked", "bombing", "bombed",
    "blast", "explosion", "exploded", "ambush", "ambushed",
    "suicide attack", "suicide bombing", "opened fire",
    "grenade attack", "terrorist attack",
]

# All attack verbs — strong indicators of an actual incident
EVENT_ATTACK_VERBS = [
    "attack", "attacked", "bombing", "bombed", "blast", "explosion",
    "exploded", "firing", "fired upon", "opened fire",
    "encounter", "ambush", "ambushed",
    "suicide attack", "suicide bombing", "grenade attack",
    "terrorist attack", "assault", "assaulted",
    "raid", "raided", "hostage",
    "infiltration",
    "stormed", "clashed", "clash",
    "detonated", "detonation",
    "kidnapped", "abducted", "assassinated",
    "set fire", "torched", "arson",
    "intercepted",
]

# casualty mentions — moderate event signal
EVENT_CASUALTY_TERMS = [
    "killed", "injured", "wounded", "dead", "died",
    "fatalities", "casualties", "martyred",
]

# weapon mentions — supporting event signal
EVENT_WEAPON_TERMS = [
    "bomb", "grenade", "explosive", "ied",
    "rifle", "firearm", "ak-47", "ak47", "rpg",
    "gun", "pistol", "machine gun", "ammunition",
    "landmine", "mine", "dynamite", "detonator",
    "rocket launcher", "suicide vest", "explosive vest",
    "arms", "weapons",
]

# attack type mentions
EVENT_ATTACK_TYPE_TERMS = [
    "bombing", "armed assault", "kidnapping", "assassination",
    "hijacking", "stabbing", "car bomb", "truck bomb",
]

# target mentions
EVENT_TARGET_TERMS = [
    "military", "army", "police", "civilian", "convoy",
    "camp", "base", "barracks", "checkpoint", "patrol",
    "jawans", "cadets", "soldiers", "troops",
    "personnel",
]


# ---------------------------------------------------------------------------
# Administrative / Investigative Exclusion Triggers
# ---------------------------------------------------------------------------
# Investigation terms — strong administrative signal
ADMIN_INVESTIGATION_TERMS = [
    "investigation revealed", "investigation disclosed",
    "further investigation", "investigation has revealed",
    "conspiracy investigation", "investigation established",
    "investigation conducted", "course of investigation",
    "during investigation", "investigation so far",
]

# Legal terms — strong administrative signal
# NOTE: Short abbreviations (FIR, IPC) are matched CASE-SENSITIVELY
# to avoid false positives (e.g. 'fir' in 'firing', 'first').
ADMIN_LEGAL_TERMS = [
    "charge-sheet", "chargesheet", "charge sheet",
    "re-registered", "fir no",
    "court proceedings", "prosecution",
    "charge stands abated", "supplementary charge-sheet",
    "supplementary chargesheet",
    "prosecution sanction", "under sections",
    "under section", "ua(p) act", "uapa",
    "nsa act", "explosive substances act",
]

# Case-sensitive legal terms (matched without lowercasing)
ADMIN_LEGAL_TERMS_CASE_SENSITIVE = [
    "FIR", "IPC",
]

# Accused list patterns
ADMIN_ACCUSED_TERMS = [
    "accused persons", "accused no",
    "a-1", "a-2", "a-3", "a-4", "a-5",
    "a-6", "a-7", "a-8", "a-9", "a-10",
    "list of accused", "names of accused",
    "absconding accused", "arrested accused",
]

# Court reference terms
ADMIN_COURT_TERMS = [
    "nia court", "sessions court", "special court",
    "judicial custody", "trial court",
    "bail", "remand", "hearing",
]

# Leadership / handler / logistics terms
ADMIN_HANDLER_TERMS = [
    "leadership handlers", "logistic support",
    "overground workers", "ogw", "handlers",
    "conspired", "conspiracy hatched",
    "radicalised", "radicalised online",
    "recruited", "recruitment",
    "facilitated the movement", "provided shelter",
    "harboured",
]


# ---------------------------------------------------------------------------
# Scoring Weights
# ---------------------------------------------------------------------------
WEIGHT_ATTACK_VERB = 2.0
WEIGHT_CASUALTY = 1.5
WEIGHT_WEAPON = 1.0
WEIGHT_ATTACK_TYPE = 1.0
WEIGHT_TARGET = 0.5

# Bonus applied when core attack verbs are present, to help event
# sentences overcome admin terms in mixed-content text (e.g. when
# spaCy merges an encounter description with an FIR registration).
CORE_ATTACK_VERB_BONUS = 3.0

WEIGHT_INVESTIGATION = 3.0
WEIGHT_LEGAL = 3.0
WEIGHT_ACCUSED = 2.0
WEIGHT_COURT = 1.5
WEIGHT_HANDLER = 2.0


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class EventDetectionResult:
    """Result of event detection scoring for a single text chunk."""
    text: str
    event_score: float
    admin_score: float
    classification: str  # "ACCEPT", "REJECT", or "NEUTRAL"
    event_triggers: list[str]
    admin_triggers: list[str]

    @property
    def is_event(self) -> bool:
        return self.classification == "ACCEPT"

    @property
    def is_administrative(self) -> bool:
        return self.classification == "REJECT"

    @property
    def is_neutral(self) -> bool:
        return self.classification == "NEUTRAL"


# ---------------------------------------------------------------------------
# Core scoring functions
# ---------------------------------------------------------------------------
def _count_matches(text: str, terms: list[str], case_sensitive: bool = False) -> Tuple[int, list[str]]:
    """
    Count the number of distinct terms found in text.
    Returns (count, list_of_matched_terms).
    
    Parameters
    ----------
    text : str
        The text to search.
    terms : list[str]
        The terms to match.
    case_sensitive : bool
        If True, match without lowercasing.
    """
    search_text = text if case_sensitive else text.lower()
    count = 0
    matched = []
    for term in terms:
        search_term = term if case_sensitive else term.lower()
        flags = 0 if case_sensitive else re.IGNORECASE
        # Use word boundary for single-word terms, simple 'in' for phrases
        if " " in search_term:
            if search_term in search_text:
                count += 1
                matched.append(term)
        else:
            if re.search(r"\b" + re.escape(search_term) + r"\b", search_text, flags):
                count += 1
                matched.append(term)
    return count, matched


def _count_core_attack_verbs(text: str) -> int:
    """Count how many core attack verbs appear in the text."""
    text_lower = text.lower()
    count = 0
    for verb in CORE_ATTACK_VERBS:
        if " " in verb:
            if verb in text_lower:
                count += 1
        else:
            if re.search(r"\b" + re.escape(verb) + r"\b", text_lower):
                count += 1
    return count


def compute_event_score(text: str) -> Tuple[float, list[str]]:
    """
    Compute the event score for a text chunk.
    
    Applies a bonus when core attack verbs (encounter, killed, bombing,
    etc.) are present. The bonus scales with the number of core verbs,
    ensuring that sentences with genuine event narratives can overcome
    co-occurring administrative terms.

    Returns
    -------
    (score, list_of_triggers)
    """
    score = 0.0
    all_triggers = []

    n, triggers = _count_matches(text, EVENT_ATTACK_VERBS)
    score += n * WEIGHT_ATTACK_VERB
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, EVENT_CASUALTY_TERMS)
    score += n * WEIGHT_CASUALTY
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, EVENT_WEAPON_TERMS)
    score += n * WEIGHT_WEAPON
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, EVENT_ATTACK_TYPE_TERMS)
    score += n * WEIGHT_ATTACK_TYPE
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, EVENT_TARGET_TERMS)
    score += n * WEIGHT_TARGET
    all_triggers.extend(triggers)

    # Core attack verb bonus — if the text contains verbs like
    # 'encounter', 'killed', 'bombing', it is very likely an actual
    # event even if admin terms are present (e.g. due to spaCy
    # merging an encounter description with an FIR reference).
    # Bonus scales with the count of core verbs found.
    core_count = _count_core_attack_verbs(text)
    if core_count > 0 and score > 0:
        score += core_count * CORE_ATTACK_VERB_BONUS
        all_triggers.append(f"[CORE_VERB_BONUS×{core_count}]")

    return score, all_triggers


def compute_admin_score(text: str) -> Tuple[float, list[str]]:
    """
    Compute the administrative/investigative score for a text chunk.

    Returns
    -------
    (score, list_of_triggers)
    """
    score = 0.0
    all_triggers = []

    n, triggers = _count_matches(text, ADMIN_INVESTIGATION_TERMS)
    score += n * WEIGHT_INVESTIGATION
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, ADMIN_LEGAL_TERMS)
    score += n * WEIGHT_LEGAL
    all_triggers.extend(triggers)

    # Case-sensitive legal terms (FIR, IPC)
    n, triggers = _count_matches(text, ADMIN_LEGAL_TERMS_CASE_SENSITIVE, case_sensitive=True)
    score += n * WEIGHT_LEGAL
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, ADMIN_ACCUSED_TERMS)
    score += n * WEIGHT_ACCUSED
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, ADMIN_COURT_TERMS)
    score += n * WEIGHT_COURT
    all_triggers.extend(triggers)

    n, triggers = _count_matches(text, ADMIN_HANDLER_TERMS)
    score += n * WEIGHT_HANDLER
    all_triggers.extend(triggers)

    return score, all_triggers


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------
def detect_event(text: str) -> EventDetectionResult:
    """
    Classify a text chunk as EVENT, ADMINISTRATIVE, or NEUTRAL.

    Parameters
    ----------
    text : str
        The text chunk (sentence or paragraph) to classify.

    Returns
    -------
    EventDetectionResult
        Contains scores, classification, and trigger details.
    """
    event_score, event_triggers = compute_event_score(text)
    admin_score, admin_triggers = compute_admin_score(text)

    # Decision logic
    if admin_score > 0 and admin_score >= event_score:
        classification = "REJECT"
    elif event_score > 0 and event_score > admin_score:
        classification = "ACCEPT"
    else:
        classification = "NEUTRAL"

    return EventDetectionResult(
        text=text,
        event_score=event_score,
        admin_score=admin_score,
        classification=classification,
        event_triggers=event_triggers,
        admin_triggers=admin_triggers,
    )


def classify_sentences(sentences: list[str]) -> list[EventDetectionResult]:
    """
    Classify a list of sentences and return their detection results.

    Parameters
    ----------
    sentences : list[str]
        The sentences to classify.

    Returns
    -------
    list[EventDetectionResult]
    """
    return [detect_event(s) for s in sentences]


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        # Event sentences
        "Two terrorists were killed in an encounter at Sunjwan, Jammu.",
        "A suicide attack by JeM militants targeted an army camp.",
        "The blast killed 40 CRPF jawans and injured several others.",

        # Administrative sentences
        "NIA filed a charge-sheet against the accused persons under sections of IPC.",
        "The FIR was re-registered and investigation revealed the conspiracy.",
        "Accused No. 1 provided logistic support to the attackers.",

        # Neutral sentences
        "The incident occurred in Jammu and Kashmir.",
        "Jaish-e-Mohammed is a Pakistan-based terrorist organization.",
    ]

    for s in samples:
        result = detect_event(s)
        print(f"Text: {s}")
        print(f"  Event Score: {result.event_score:.1f} | Admin Score: {result.admin_score:.1f}")
        print(f"  Classification: {result.classification}")
        print(f"  Event Triggers: {result.event_triggers}")
        print(f"  Admin Triggers: {result.admin_triggers}")
        print()
