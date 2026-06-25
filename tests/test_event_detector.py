"""
Unit Tests — Event Detector
============================

Tests the event detection scoring and classification logic.
"""

import os
import sys
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.event_detector import (
    detect_event,
    compute_event_score,
    compute_admin_score,
    classify_sentences,
)


# ===================================================================
# Test: Event sentences → ACCEPT
# ===================================================================
class TestEventAccept:
    """Sentences describing actual attacks/events should be classified as ACCEPT."""

    def test_encounter_with_casualties(self):
        result = detect_event("Two terrorists were killed in an encounter at Sunjwan army camp.")
        assert result.classification == "ACCEPT"
        assert result.event_score > result.admin_score

    def test_bombing_attack(self):
        result = detect_event("A car bomb exploded near a police checkpoint killing 5 officers.")
        assert result.classification == "ACCEPT"

    def test_suicide_attack(self):
        result = detect_event("A suicide attack by JeM militants targeted the CRPF convoy.")
        assert result.classification == "ACCEPT"

    def test_armed_assault(self):
        result = detect_event("Gunmen opened fire on the army base injuring several soldiers.")
        assert result.classification == "ACCEPT"

    def test_grenade_attack(self):
        result = detect_event("A grenade attack on a bus stand in Srinagar wounded 15 civilians.")
        assert result.classification == "ACCEPT"

    def test_ambush(self):
        result = detect_event("Militants ambushed a military patrol near the Line of Control.")
        assert result.classification == "ACCEPT"

    def test_infiltration_with_attack(self):
        result = detect_event("Terrorists infiltrated the army camp and attacked the residential area.")
        assert result.classification == "ACCEPT"

    def test_blast_with_casualties(self):
        result = detect_event("The blast killed 40 CRPF jawans and injured several others on the highway.")
        assert result.classification == "ACCEPT"


# ===================================================================
# Test: Administrative sentences → REJECT
# ===================================================================
class TestAdminReject:
    """Sentences describing investigations, legal proceedings, etc. should be REJECT."""

    def test_chargesheet_filing(self):
        result = detect_event("NIA filed a charge-sheet against the accused persons under sections of IPC and UA(P) Act.")
        assert result.classification == "REJECT"

    def test_fir_registration(self):
        result = detect_event("An FIR was re-registered at Sunjwan police station.")
        assert result.classification == "REJECT"

    def test_investigation_revealed(self):
        result = detect_event("Investigation revealed that the conspiracy was hatched in Pakistan.")
        assert result.classification == "REJECT"

    def test_accused_list(self):
        result = detect_event("Accused No. 1 (A-1) Mufti Mohamad Yaseen provided logistic support to the attackers.")
        assert result.classification == "REJECT"

    def test_court_proceedings(self):
        result = detect_event("The NIA Court took cognizance of the charge-sheet filed in the case.")
        assert result.classification == "REJECT"

    def test_prosecution(self):
        result = detect_event("Prosecution sanction was obtained under UA(P) Act sections.")
        assert result.classification == "REJECT"

    def test_further_investigation(self):
        result = detect_event("Further investigation is in progress to identify the handlers.")
        assert result.classification == "REJECT"

    def test_charge_abated(self):
        result = detect_event("The charge stands abated against the two deceased terrorists.")
        assert result.classification == "REJECT"

    def test_overground_workers(self):
        result = detect_event("The overground workers provided shelter and facilitated the movement of the terrorists.")
        assert result.classification == "REJECT"


# ===================================================================
# Test: Neutral sentences → NEUTRAL
# ===================================================================
class TestNeutral:
    """Sentences with neither event nor admin signal should be NEUTRAL."""

    def test_location_only(self):
        result = detect_event("The incident occurred in Jammu and Kashmir, India.")
        assert result.classification == "NEUTRAL"

    def test_organization_description(self):
        result = detect_event("Jaish-e-Mohammed is a Pakistan-based terrorist organization.")
        assert result.classification == "NEUTRAL"

    def test_date_only(self):
        result = detect_event("On February 10, 2018, the weather was clear in Jammu.")
        assert result.classification == "NEUTRAL"

    def test_boilerplate(self):
        result = detect_event("This document has been prepared by the National Investigation Agency.")
        assert result.classification == "NEUTRAL"


# ===================================================================
# Test: Mixed sentences — score comparison
# ===================================================================
class TestMixedContent:
    """Sentences with both event and admin terms should be classified by score comparison."""

    def test_admin_dominates(self):
        text = "The charge-sheet details how the accused persons conspired and the FIR was re-registered after investigation revealed the conspiracy."
        result = detect_event(text)
        assert result.admin_score >= result.event_score
        assert result.classification == "REJECT"

    def test_event_dominates(self):
        text = "The terrorists attacked the army camp and killed two soldiers during the encounter before being killed themselves."
        result = detect_event(text)
        assert result.event_score > result.admin_score
        assert result.classification == "ACCEPT"


# ===================================================================
# Test: Scoring functions independently
# ===================================================================
class TestScoringFunctions:
    """Verify individual scoring functions return correct weights."""

    def test_event_score_attack_verbs(self):
        score, triggers = compute_event_score("The militants attacked and then bombed the area.")
        assert "attacked" in triggers
        assert score >= 2.0  # at least one attack verb

    def test_event_score_casualties(self):
        score, triggers = compute_event_score("Three soldiers were killed and five were injured.")
        assert "killed" in triggers
        assert "injured" in triggers
        assert score >= 3.0  # at least two casualty terms × 1.5

    def test_admin_score_legal_terms(self):
        score, triggers = compute_admin_score("A charge-sheet was filed under sections of IPC.")
        assert "charge-sheet" in triggers
        assert score >= 3.0  # at least one legal term × 3.0

    def test_admin_score_investigation(self):
        score, triggers = compute_admin_score("Investigation revealed the conspiracy details.")
        assert "investigation revealed" in triggers
        assert score >= 3.0


# ===================================================================
# Test: Batch classification
# ===================================================================
class TestClassifySentences:
    """Test the batch classification function."""

    def test_batch_mixed(self):
        sentences = [
            "Two terrorists were killed in an encounter.",          # ACCEPT
            "NIA filed a charge-sheet against accused persons.",     # REJECT
            "The incident occurred in Jammu.",                       # NEUTRAL
        ]
        results = classify_sentences(sentences)
        assert len(results) == 3
        assert results[0].classification == "ACCEPT"
        assert results[1].classification == "REJECT"
        assert results[2].classification == "NEUTRAL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
