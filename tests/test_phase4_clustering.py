"""
Tests for Phase 4: Event Discovery and Incident Clustering
"""

import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.document import Document
from extraction.clustering.multi_incident_builder import build_multi_incidents

class TestClustering(unittest.TestCase):

    def setUp(self):
        # We just need a dummy doc_id
        self.doc_id = "test_doc_123"

    def test_case_1_single_incident(self):
        """Case 1: Single incident document -> Expected 1 incident"""
        text = "Militants attacked a CRPF convoy in Pulwama today. 3 personnel were killed in the bombing."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].killed, 3)
        self.assertEqual(incidents[0].city, "Pulwama")
        self.assertIn("Bombing", incidents[0].attack_types)

    def test_case_2_two_incidents_same_date_diff_locations(self):
        """Case 2: Two incidents same date different locations -> Expected 2 incidents"""
        text = "On January 15, militants attacked a checkpoint in Srinagar. Meanwhile, on January 15, an IED exploded in Shopian."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 2)
        cities = {inc.city for inc in incidents}
        self.assertIn("Srinagar", cities)
        self.assertIn("Shopian", cities)

    def test_case_3_two_incidents_same_location_diff_dates(self):
        """Case 3: Two incidents same location different dates -> Expected 2 incidents"""
        text = "On January 15, militants attacked a checkpoint in Srinagar. The following week, on January 22, an IED exploded in Srinagar."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        # Because the dates differ entirely, and they are both anchors, it should split
        self.assertEqual(len(incidents), 2)

    def test_case_4_one_attack_followed_by_casualty_details(self):
        """Case 4: One attack followed by casualty details -> Expected 1 incident"""
        text = "Militants attacked a CRPF convoy in Pulwama on January 15. The blast was massive. Later hospital reports confirmed that 40 soldiers were killed. JeM claimed responsibility."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].killed, 40)
        self.assertIn("JeM", incidents[0].responsible_groups)

    def test_case_5_daily_briefing(self):
        """Case 5: Daily intelligence briefing containing 3 separate incidents -> Expected 3 incidents"""
        text = (
            "Daily SITREP. "
            "In Pulwama, militants attacked a CRPF convoy killing 3. "
            "Separately, security forces neutralized 2 militants in an encounter in Shopian. "
            "Finally, an unknown group kidnapped a local official in Baramulla."
        )
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 3)
        cities = {inc.city for inc in incidents}
        self.assertIn("Pulwama", cities)
        self.assertIn("Shopian", cities)
        self.assertIn("Baramulla", cities)

    def test_case_6_context_window_resolution(self):
        """Case 6: Location in sent 1, casualties in sent 2. Should merge and share location."""
        text = "An IED exploded in Pulwama today. 3 soldiers were killed in the blast."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].city, "Pulwama")
        self.assertEqual(incidents[0].killed, 3)

    def test_case_7_narrative_boundary_force_split(self):
        """Case 7: Force split via narrative boundary despite same city."""
        text = "Militants attacked a convoy in Srinagar. Meanwhile, an encounter started in another part of Srinagar."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        self.assertEqual(len(incidents), 2)

    def test_case_8_attack_mismatch_force_split(self):
        """Case 8: Force split due to completely different operation/attack types and actors."""
        text = "Lashkar-e-Taiba bombed a hospital. Police later arrested 5 Jaish-e-Mohammed operatives."
        doc = Document(self.doc_id, "TXT", "", text)
        incidents = build_multi_incidents(doc)
        # Should split because attack type mismatch (Bombing vs Arrest/Operation) and Actor mismatch (LeT vs JeM)
        self.assertEqual(len(incidents), 2)


if __name__ == "__main__":
    unittest.main()
