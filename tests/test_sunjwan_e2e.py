"""
End-to-End Pipeline Test — Sunjwan Terrorist Attack
=====================================================

Regression test to verify that the Sunjwan NIA document produces
exactly ONE incident after the full pipeline processes it.

This test:
  1. Ingests the Sunjwan PDF
  2. Shows intermediate outputs (chunking, event detection, candidates)
  3. Asserts exactly 1 final incident
  4. Validates incident fields (location, group, attack type, casualties)
"""

import os
import sys
import pytest

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline import ingest
from extraction.event_detector import detect_event, classify_sentences
from extraction.clustering.multi_incident_builder import build_multi_incidents

import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


# Path to the test PDF
SUNJWAN_PDF = os.path.join(PROJECT_ROOT, "test_files", "sunjawan terrorist attack.pdf")


# ===================================================================
# Helper: Print intermediate outputs
# ===================================================================
def _print_pipeline_trace(document):
    """
    Print detailed intermediate outputs for debugging.
    Shows: chunking → event detection → incident building.
    """
    text = document.raw_text
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]

    print("\n" + "=" * 80)
    print("  PIPELINE TRACE — Sunjwan Terrorist Attack")
    print("=" * 80)

    # --- Chunking Output ---
    print(f"\n  [1] CHUNKING: {len(sentences)} sentences extracted")
    print("-" * 80)
    for i, sent in enumerate(sentences[:30]):  # Show first 30
        print(f"  [{i:3d}] {sent[:120]}{'...' if len(sent) > 120 else ''}")
    if len(sentences) > 30:
        print(f"  ... ({len(sentences) - 30} more sentences)")

    # --- Event Detection Output ---
    print(f"\n  [2] EVENT DETECTION:")
    print("-" * 80)
    accept_count = 0
    reject_count = 0
    neutral_count = 0

    for i, sent in enumerate(sentences):
        result = detect_event(sent)
        status_icon = {
            "ACCEPT": "✅",
            "REJECT": "❌",
            "NEUTRAL": "⚪",
        }[result.classification]

        if result.classification == "ACCEPT":
            accept_count += 1
        elif result.classification == "REJECT":
            reject_count += 1
        else:
            neutral_count += 1

        # Print all non-neutral sentences for debugging
        if result.classification != "NEUTRAL" or i < 20:
            print(f"  {status_icon} [{i:3d}] {result.classification:7s} "
                  f"(E={result.event_score:4.1f} A={result.admin_score:4.1f}) "
                  f"{sent[:100]}{'...' if len(sent) > 100 else ''}")
            if result.event_triggers:
                print(f"         Event triggers: {result.event_triggers}")
            if result.admin_triggers:
                print(f"         Admin triggers: {result.admin_triggers}")

    print(f"\n  Summary: {accept_count} ACCEPT, {reject_count} REJECT, {neutral_count} NEUTRAL")

    # --- Incident Building Output ---
    print(f"\n  [3] INCIDENT BUILDING (after deduplication):")
    print("-" * 80)
    incidents = build_multi_incidents(document)
    print(f"  Total incidents produced: {len(incidents)}")

    for idx, inc in enumerate(incidents, 1):
        print(f"\n  --- Incident {idx} ---")
        print(f"    Date:             {inc.date or '(none)'}")
        print(f"    Country:          {inc.country or '(none)'}")
        print(f"    State:            {inc.state or '(none)'}")
        print(f"    City:             {inc.city or '(none)'}")
        print(f"    Attack Types:     {inc.attack_types or '(none)'}")
        print(f"    Weapon Types:     {inc.weapon_types or '(none)'}")
        print(f"    Target Types:     {inc.target_types or '(none)'}")
        print(f"    Responsible:      {inc.responsible_groups or '(none)'}")
        print(f"    Killed:           {inc.killed}")
        print(f"    Injured:          {inc.injured}")
        print(f"    Summary:          {inc.summary[:200]}{'...' if len(inc.summary) > 200 else ''}")

    print("\n" + "=" * 80)
    return incidents


# ===================================================================
# Test: PDF exists
# ===================================================================
class TestSunjwanPDFExists:

    def test_pdf_file_exists(self):
        """Verify the test PDF is available."""
        assert os.path.isfile(SUNJWAN_PDF), (
            f"Sunjwan test PDF not found at: {SUNJWAN_PDF}"
        )


# ===================================================================
# Test: Ingestion works
# ===================================================================
class TestSunjwanIngestion:

    def test_ingestion_produces_document(self):
        """Ingestion should produce a valid Document object."""
        doc = ingest(SUNJWAN_PDF)
        assert doc is not None
        assert len(doc.raw_text) > 100

    def test_document_has_text(self):
        """Document should contain meaningful text."""
        doc = ingest(SUNJWAN_PDF)
        text_lower = doc.raw_text.lower()
        # Should contain keywords related to the Sunjwan attack
        assert any(kw in text_lower for kw in ["sunjwan", "sunjawan", "jammu"])


# ===================================================================
# Test: Event Detection on Sunjwan text
# ===================================================================
class TestSunjwanEventDetection:

    def test_has_event_sentences(self):
        """The document should have at least one ACCEPT (event) sentence."""
        doc = ingest(SUNJWAN_PDF)
        sentences_doc = nlp(doc.raw_text)
        sentences = [s.text.strip() for s in sentences_doc.sents if len(s.text.strip()) > 10]
        results = classify_sentences(sentences)

        accept_count = sum(1 for r in results if r.classification == "ACCEPT")
        assert accept_count >= 1, "Expected at least 1 event sentence"

    def test_has_rejected_sentences(self):
        """The document should have some REJECT (administrative) sentences."""
        doc = ingest(SUNJWAN_PDF)
        sentences_doc = nlp(doc.raw_text)
        sentences = [s.text.strip() for s in sentences_doc.sents if len(s.text.strip()) > 10]
        results = classify_sentences(sentences)

        reject_count = sum(1 for r in results if r.classification == "REJECT")
        assert reject_count >= 1, "Expected at least 1 administrative sentence"


# ===================================================================
# Test: CRITICAL — Final incident count
# ===================================================================
class TestSunjwanFinalOutput:

    def test_exactly_one_incident(self):
        """
        REGRESSION TEST: The Sunjwan document should produce exactly ONE
        consolidated incident, not multiple chunk-derived incidents.

        This is the core assertion that validates the event-centric redesign.
        """
        doc = ingest(SUNJWAN_PDF)
        incidents = build_multi_incidents(doc)

        # Print trace for debugging (visible with pytest -s)
        print(f"\n  SUNJWAN TEST: {len(incidents)} incident(s) produced")
        for idx, inc in enumerate(incidents, 1):
            print(f"    Incident {idx}: {inc.city}, {inc.state} — {inc.attack_types} — killed={inc.killed}")

        assert len(incidents) == 1, (
            f"Expected exactly 1 incident from Sunjwan PDF, got {len(incidents)}. "
            f"The event-centric pipeline should consolidate all event-bearing "
            f"sentences into a single incident."
        )

    def test_incident_location(self):
        """The incident should reference Sunjwan/Jammu/J&K."""
        doc = ingest(SUNJWAN_PDF)
        incidents = build_multi_incidents(doc)
        assert len(incidents) >= 1

        inc = incidents[0]
        location_text = f"{inc.city} {inc.state} {inc.country}".lower()
        assert any(kw in location_text for kw in ["sunjwan", "sunjawan", "jammu"]), (
            f"Expected Sunjwan/Jammu in location, got: city={inc.city}, state={inc.state}"
        )

    def test_incident_responsible_group(self):
        """The incident should identify JeM as responsible."""
        doc = ingest(SUNJWAN_PDF)
        incidents = build_multi_incidents(doc)
        assert len(incidents) >= 1

        inc = incidents[0]
        groups_lower = [g.lower() for g in inc.responsible_groups]
        groups_text = " ".join(groups_lower)
        assert any(kw in groups_text for kw in ["jem", "jaish", "jaish-e-mohammed"]), (
            f"Expected JeM in responsible groups, got: {inc.responsible_groups}"
        )

    def test_incident_has_casualties(self):
        """The incident should report casualties (at least killed > 0)."""
        doc = ingest(SUNJWAN_PDF)
        incidents = build_multi_incidents(doc)
        assert len(incidents) >= 1

        inc = incidents[0]
        assert inc.killed > 0, (
            f"Expected killed > 0, got killed={inc.killed}"
        )

    def test_incident_has_attack_type(self):
        """The incident should have an attack type classification."""
        doc = ingest(SUNJWAN_PDF)
        incidents = build_multi_incidents(doc)
        assert len(incidents) >= 1

        inc = incidents[0]
        assert len(inc.attack_types) > 0, (
            f"Expected at least one attack type, got: {inc.attack_types}"
        )


# ===================================================================
# Test: Full pipeline trace (run with pytest -s for output)
# ===================================================================
class TestSunjwanPipelineTrace:

    def test_print_pipeline_trace(self):
        """
        Print the full pipeline trace for manual inspection.
        Run with: pytest tests/test_sunjwan_e2e.py::TestSunjwanPipelineTrace -s -v
        """
        doc = ingest(SUNJWAN_PDF)
        incidents = _print_pipeline_trace(doc)
        # This test always passes — it's for inspection only
        assert True


if __name__ == "__main__":
    # When run directly, show the full trace
    print("\n  Loading Sunjwan PDF for end-to-end test...")
    doc = ingest(SUNJWAN_PDF)
    if doc:
        incidents = _print_pipeline_trace(doc)
        print(f"\n  FINAL RESULT: {len(incidents)} incident(s)")
        if len(incidents) == 1:
            print("  ✅ PASS — Single incident produced (as expected)")
        else:
            print(f"  ❌ FAIL — Expected 1 incident, got {len(incidents)}")
    else:
        print("  ❌ FAIL — Could not ingest document")
