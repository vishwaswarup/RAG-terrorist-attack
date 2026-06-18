"""
Attack, Weapon, and Target Classifier
=======================================

Classifies incident text into controlled vocabulary categories
using keyword matching and rule-based logic.

No ML or LLM — purely keyword-driven.
"""

import re

# ---------------------------------------------------------------------------
# Controlled Vocabularies
# ---------------------------------------------------------------------------
# Each maps a category name → list of keywords/phrases to search for.
# All matching is case-insensitive.

ATTACK_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Bombing": [
        "bomb", "bombing", "blast", "explosion", "exploded",
        "detonated", "detonation", "ied", "car bomb", "suicide bomb",
        "truck bomb", "improvised explosive", "suicide bomber",
        "explosive device", "explosive vest",
    ],
    "Armed Assault": [
        "shooting", "gunfire", "gunmen", "opened fire", "shot dead",
        "armed assault", "armed attack", "firefight", "shoot-out",
        "gunshot", "machine gun", "rifle fire",
        "fired upon", "fired on",
        "stormed", "breached", "assault",
        "armed militants", "armed attackers",
        "attacked", "gunfight",
    ],
    "Kidnapping": [
        "kidnap", "kidnapping", "abducted", "abduction",
        "taken hostage", "hostage", "seized", "captured",
    ],
    "Assassination": [
        "assassination", "assassinated", "targeted killing",
        "shot and killed", "gunned down",
    ],
    "Hijacking": [
        "hijack", "hijacking", "hijacked", "commandeered",
        "took control of",
    ],
    "Arson": [
        "arson", "set fire", "set ablaze", "torched", "firebomb",
        "burned down", "set on fire", "vandalized", "sabotage",
        "destroyed", "damaged",
    ],
    "Stabbing": [
        "stabbing", "stabbed", "knife attack", "machete",
        "slashing", "hacked",
    ],
    "Unarmed Assault": [
        "unarmed assault", "beaten", "punched", "kicked",
        "assaulted with bare hands", "mob violence", "lynched",
    ],
}

WEAPON_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Explosives": [
        "bomb", "explosive", "ied", "dynamite", "tnt", "grenade",
        "landmine", "mine", "detonator", "c4", "semtex",
        "improvised explosive device", "grenades", "blasts",
        "explosive device", "explosive vest", "suicide vest",
        "rocket launcher", "rocket launchers", "rpg",
        "blast",
    ],
    "Firearms": [
        "gun", "rifle", "pistol", "ak-47", "ak47", "firearm",
        "machine gun", "assault rifle", "assault rifles", "shotgun",
        "automatic weapon", "automatic weapons",
        "kalashnikov", "ammunition", "bullets",
        "opened fire", "fired upon", "fired on", "firing",
        "gunfire", "gunmen", "gunshot", "gunfight",
        "armed with", "armed militants", "armed attackers",
        "shooting",
    ],
    "Melee": [
        "knife", "machete", "sword", "axe", "blade", "dagger",
        "sharp weapon", "blunt object",
    ],
    "Vehicle": [
        "car bomb", "truck bomb", "vbied",
        "vehicle-borne", "rammed", "vehicle attack", "ramming attack",
        "drove into",
    ],
    "Chemical": [
        "chemical", "nerve agent", "sarin", "mustard gas",
        "chlorine", "toxic gas", "poison gas", "poison", "acid",
        "chemical agent",
    ],
    "Incendiary": [
        "molotov", "firebomb", "incendiary", "petrol bomb",
    ],
    "Sabotage Equipment": [
        "sabotage equipment", "tools", "wrench", "bolt cutter",
    ],
}

TARGET_TYPE_KEYWORDS: dict[str, list[str]] = {
    "Military": [
        "military", "soldier", "soldiers", "troops", "barracks",
        "naval", "defense", "defence",
        "checkpoint", "convoy", "military convoys", "patrol",
        "army camp", "army base", "air force base",
        "jawans", "cadets",
    ],
    "Government": [
        "government", "parliament", "embassy", "consulate",
        "police", "police station", "courthouse", "minister",
        "official", "diplomat", "prison", "checkpoints",
    ],
    "Religious": [
        "church", "mosque", "temple", "synagogue", "shrine",
        "cathedral", "religious", "worship", "prayer",
        "pilgrim", "pilgrims", "pilgrimage", "religious buildings",
    ],
    "Civilian": [
        "civilian", "civilians", "market", "marketplace", "shops", "stores",
        "passenger", "passengers", "commuter", "commuters",
        "crowd", "crowds", "gathering", "festival",
        "concert", "school", "schools", "university", "universities",
        "colleges", "hospital", "hotel", "bank", "factory",
        "restaurant", "cafe", "shopping", "business",
        "families", "children", "people",
        "foreign nationals", "nationals",
        "spectators",
    ],
    "Infrastructure": [
        "infrastructure", "pipeline", "power plant", "dam",
        "bridge", "railway", "port", "telecom", "power stations",
        "telecom towers", "pylon", "oil facility", "refinery",
        "utilities",
    ],
    "Media": [
        "journalist", "reporter", "media", "newspaper",
        "news agency", "press", "broadcaster",
    ],
    "Transportation": [
        "bus", "train", "airplane", "aircraft", "flight",
        "ferry", "ship", "subway", "metro",
        "airport", "railway station", "terminus",
    ],
}


def _match_keywords(text: str, vocabulary: dict[str, list[str]]) -> list[str]:
    """
    Search text for keywords from a vocabulary and return
    all matching category names.
    """
    text_lower = text.lower()
    matched = []
    for category, keywords in vocabulary.items():
        for keyword in keywords:
            # Use word-boundary regex for short keywords,
            # simple 'in' for phrases (2+ words)
            if " " in keyword:
                if keyword in text_lower:
                    matched.append(category)
                    break
            else:
                if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
                    matched.append(category)
                    break
    return matched


def extract_attack_types(text: str) -> list[str]:
    """
    Classify the attack type(s) from text.

    Returns a list of matching categories from the controlled vocabulary.
    Example: ["Bombing", "Armed Assault"]
    """
    return _match_keywords(text, ATTACK_TYPE_KEYWORDS)


def extract_weapon_types(text: str) -> list[str]:
    """
    Classify the weapon type(s) from text.

    Returns a list of matching categories.
    Example: ["Explosives", "Firearms"]
    """
    return _match_keywords(text, WEAPON_TYPE_KEYWORDS)


def extract_target_types(text: str) -> list[str]:
    """
    Classify the target type(s) from text.

    Returns a list of matching categories.
    Example: ["Religious", "Civilian"]
    """
    return _match_keywords(text, TARGET_TYPE_KEYWORDS)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = (
        "A suicide bomb exploded near a church in the city centre, "
        "killing 45 civilians. Gunmen then opened fire on the crowd. "
        "Police responded to the scene."
    )

    print(f"Text: {sample}\n")
    print(f"  Attack Types : {extract_attack_types(sample)}")
    print(f"  Weapon Types : {extract_weapon_types(sample)}")
    print(f"  Target Types : {extract_target_types(sample)}")
