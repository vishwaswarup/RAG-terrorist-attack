"""
Unit Tests — Incident Deduplicator
====================================

Tests the incident deduplication and merging logic.
"""

import os
import sys
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.incident import Incident
from extraction.incident_deduplicator import (
    deduplicate_incidents,
    _should_merge,
    _dates_match,
    _locations_match,
    _groups_overlap,
    _jaccard_similarity,
    _texts_similar,
    _merge_incidents,
)


# ===================================================================
# Helpers
# ===================================================================
def _make_incident(**kwargs) -> Incident:
    """Helper to create incidents with defaults."""
    defaults = {
        "incident_id": "inc-test",
        "date": "",
        "country": "",
        "state": "",
        "city": "",
        "location_confidence": 0.0,
        "attack_types": [],
        "target_types": [],
        "weapon_types": [],
        "responsible_groups": [],
        "target_organizations": [],
        "killed": 0,
        "injured": 0,
        "summary": "",
        "source_document_id": "doc-test",
    }
    defaults.update(kwargs)
    return Incident(**defaults)


# ===================================================================
# Test: Date matching
# ===================================================================
class TestDateMatching:

    def test_same_date(self):
        assert _dates_match("2018-02-10", "2018-02-10") is True

    def test_adjacent_dates(self):
        assert _dates_match("2018-02-10", "2018-02-11") is True

    def test_far_dates(self):
        assert _dates_match("2018-02-10", "2018-03-15") is False

    def test_empty_date(self):
        assert _dates_match("", "2018-02-10") is False
        assert _dates_match("2018-02-10", "") is False
        assert _dates_match("", "") is False


# ===================================================================
# Test: Location matching
# ===================================================================
class TestLocationMatching:

    def test_same_city(self):
        inc1 = _make_incident(city="Sunjwan")
        inc2 = _make_incident(city="Sunjwan")
        assert _locations_match(inc1, inc2) is True

    def test_case_insensitive_city(self):
        inc1 = _make_incident(city="sunjwan")
        inc2 = _make_incident(city="Sunjwan")
        assert _locations_match(inc1, inc2) is True

    def test_different_city(self):
        inc1 = _make_incident(city="Sunjwan")
        inc2 = _make_incident(city="Pulwama")
        assert _locations_match(inc1, inc2) is False

    def test_same_state_no_city(self):
        inc1 = _make_incident(state="Jammu and Kashmir")
        inc2 = _make_incident(state="Jammu and Kashmir")
        assert _locations_match(inc1, inc2) is True

    def test_no_location(self):
        inc1 = _make_incident()
        inc2 = _make_incident()
        assert _locations_match(inc1, inc2) is False


# ===================================================================
# Test: Group overlap
# ===================================================================
class TestGroupOverlap:

    def test_same_group(self):
        inc1 = _make_incident(responsible_groups=["Jaish-e-Mohammed"])
        inc2 = _make_incident(responsible_groups=["Jaish-e-Mohammed"])
        assert _groups_overlap(inc1, inc2) is True

    def test_overlapping_groups(self):
        inc1 = _make_incident(responsible_groups=["JeM", "ISIS"])
        inc2 = _make_incident(responsible_groups=["JeM"])
        assert _groups_overlap(inc1, inc2) is True

    def test_different_groups(self):
        inc1 = _make_incident(responsible_groups=["JeM"])
        inc2 = _make_incident(responsible_groups=["LeT"])
        assert _groups_overlap(inc1, inc2) is False

    def test_empty_groups(self):
        inc1 = _make_incident(responsible_groups=[])
        inc2 = _make_incident(responsible_groups=["JeM"])
        assert _groups_overlap(inc1, inc2) is False


# ===================================================================
# Test: Jaccard similarity
# ===================================================================
class TestJaccardSimilarity:

    def test_identical_texts(self):
        sim = _jaccard_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_completely_different(self):
        sim = _jaccard_similarity("hello world", "foo bar baz")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = _jaccard_similarity(
            "terrorists killed in encounter at army camp",
            "encounter at army camp where terrorists attacked"
        )
        assert sim > 0.3  # significant overlap

    def test_empty_text(self):
        assert _jaccard_similarity("", "hello") == 0.0
        assert _jaccard_similarity("hello", "") == 0.0


# ===================================================================
# Test: Should merge logic
# ===================================================================
class TestShouldMerge:

    def test_two_criteria_met(self):
        """Same date + same city → merge."""
        inc1 = _make_incident(date="2018-02-10", city="Sunjwan")
        inc2 = _make_incident(date="2018-02-10", city="Sunjwan")
        assert _should_merge(inc1, inc2) is True

    def test_one_criterion_met(self):
        """Only same date → don't merge."""
        inc1 = _make_incident(date="2018-02-10", city="Sunjwan")
        inc2 = _make_incident(date="2018-02-10", city="Pulwama")
        assert _should_merge(inc1, inc2) is False

    def test_date_and_group(self):
        """Same date + same group → merge."""
        inc1 = _make_incident(date="2018-02-10", responsible_groups=["JeM"])
        inc2 = _make_incident(date="2018-02-10", responsible_groups=["JeM"])
        assert _should_merge(inc1, inc2) is True

    def test_city_and_group(self):
        """Same city + same group → merge."""
        inc1 = _make_incident(city="Sunjwan", responsible_groups=["JeM"])
        inc2 = _make_incident(city="Sunjwan", responsible_groups=["JeM"])
        assert _should_merge(inc1, inc2) is True

    def test_no_criteria_met(self):
        """Nothing matches → don't merge."""
        inc1 = _make_incident(date="2018-02-10", city="Sunjwan")
        inc2 = _make_incident(date="2019-05-01", city="Pulwama")
        assert _should_merge(inc1, inc2) is False


# ===================================================================
# Test: Merge incidents
# ===================================================================
class TestMergeIncidents:

    def test_casualty_max(self):
        inc1 = _make_incident(incident_id="inc-1", killed=2, injured=0)
        inc2 = _make_incident(incident_id="inc-2", killed=0, injured=5)
        merged = _merge_incidents(inc1, inc2)
        assert merged.killed == 2
        assert merged.injured == 5

    def test_group_union(self):
        inc1 = _make_incident(incident_id="inc-1", responsible_groups=["JeM"])
        inc2 = _make_incident(incident_id="inc-2", responsible_groups=["Jaish-e-Mohammed"])
        merged = _merge_incidents(inc1, inc2)
        assert set(merged.responsible_groups) == {"JeM", "Jaish-e-Mohammed"}

    def test_location_preference(self):
        """Primary with city wins over secondary without."""
        inc1 = _make_incident(incident_id="inc-1", city="Sunjwan", state="Jammu and Kashmir")
        inc2 = _make_incident(incident_id="inc-2", city="", state="Jammu and Kashmir")
        merged = _merge_incidents(inc1, inc2)
        assert merged.city == "Sunjwan"

    def test_date_earliest(self):
        inc1 = _make_incident(incident_id="inc-1", date="2018-02-11")
        inc2 = _make_incident(incident_id="inc-2", date="2018-02-10")
        merged = _merge_incidents(inc1, inc2)
        assert merged.date == "2018-02-10"

    def test_keeps_primary_id(self):
        inc1 = _make_incident(incident_id="inc-primary")
        inc2 = _make_incident(incident_id="inc-secondary")
        merged = _merge_incidents(inc1, inc2)
        assert merged.incident_id == "inc-primary"

    def test_attack_types_union(self):
        inc1 = _make_incident(incident_id="inc-1", attack_types=["Armed Assault"])
        inc2 = _make_incident(incident_id="inc-2", attack_types=["Bombing"])
        merged = _merge_incidents(inc1, inc2)
        assert set(merged.attack_types) == {"Armed Assault", "Bombing"}


# ===================================================================
# Test: Full deduplication pipeline
# ===================================================================
class TestDeduplicateIncidents:

    def test_no_duplicates(self):
        """Distinct incidents should remain separate."""
        incidents = [
            _make_incident(incident_id="inc-1", date="2018-02-10", city="Sunjwan"),
            _make_incident(incident_id="inc-2", date="2019-02-14", city="Pulwama"),
        ]
        result = deduplicate_incidents(incidents)
        assert len(result) == 2

    def test_duplicates_merged(self):
        """Same-event incidents should merge."""
        incidents = [
            _make_incident(
                incident_id="inc-1", date="2018-02-10", city="Sunjwan",
                responsible_groups=["JeM"], killed=2
            ),
            _make_incident(
                incident_id="inc-2", date="2018-02-10", city="Sunjwan",
                responsible_groups=["Jaish-e-Mohammed"], killed=0,
                weapon_types=["Firearms"]
            ),
        ]
        result = deduplicate_incidents(incidents)
        assert len(result) == 1
        assert result[0].killed == 2
        assert "Firearms" in result[0].weapon_types

    def test_single_incident(self):
        """Single incident should pass through unchanged."""
        incidents = [_make_incident(incident_id="inc-1")]
        result = deduplicate_incidents(incidents)
        assert len(result) == 1

    def test_empty_list(self):
        result = deduplicate_incidents([])
        assert len(result) == 0

    def test_three_duplicates_merged(self):
        """Three incidents for the same event should merge to one."""
        incidents = [
            _make_incident(
                incident_id="inc-1", date="2018-02-10", city="Sunjwan",
                responsible_groups=["JeM"], killed=2
            ),
            _make_incident(
                incident_id="inc-2", date="2018-02-10", city="Sunjwan",
                responsible_groups=["JeM"], attack_types=["Armed Assault"]
            ),
            _make_incident(
                incident_id="inc-3", date="2018-02-10", city="Sunjwan",
                weapon_types=["Firearms"], injured=3
            ),
        ]
        result = deduplicate_incidents(incidents)
        assert len(result) == 1
        assert result[0].killed == 2
        assert result[0].injured == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
