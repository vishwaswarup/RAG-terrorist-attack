"""
Event Anchor Detector
=====================
Determines if a sentence describes the core of an attack/incident.
"""

import re
from typing import List

# Expanded Anchor Vocabulary
ATTACK_ANCHORS = [
    "attack", "attacked", "ambush", "ambushed", "bombing", "bombed", "explosion",
    "exploded", "opened fire", "grenade attack", "kidnapping", "kidnapped",
    "abduction", "abducted", "assassination", "assassinated", "arson",
    "set fire", "torched", "blast", "clash", "clashed"
]

CASUALTY_ANCHORS = [
    "killed", "injured", "wounded", "fatalities", "casualties", "dead", "died"
]

WEAPON_ANCHORS = [
    "ied", "grenade", "explosive", "mine", "rpg", "ak-47", "rifle", "firearm"
]

OPERATION_ANCHORS = [
    "encounter", "raid", "raided", "search operation", "neutralized", 
    "arrested", "detained"
]

ALL_ANCHORS = ATTACK_ANCHORS + CASUALTY_ANCHORS + WEAPON_ANCHORS + OPERATION_ANCHORS

NARRATIVE_BOUNDARIES = [
    "meanwhile", "separately", "elsewhere", "in a separate incident",
    "another attack", "additionally", "in another incident"
]

def is_anchor_sentence(text: str) -> bool:
    """Returns True if the text contains explicit event anchor keywords."""
    text_lower = text.lower()
    for keyword in ALL_ANCHORS:
        # Avoid matching 'IED' inside 'died' by enforcing boundaries
        # Weapon anchors might not need word boundaries if they are specific, but safe to use.
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
            return True
    return False

def has_narrative_boundary(text: str) -> bool:
    """Returns True if the text begins or contains explicit narrative splits."""
    text_lower = text.lower()
    for boundary in NARRATIVE_BOUNDARIES:
        if re.search(r"\b" + re.escape(boundary) + r"\b", text_lower):
            return True
    return False

def detect_anchors(sentences: List[str]) -> List[bool]:
    return [is_anchor_sentence(s) for s in sentences]
