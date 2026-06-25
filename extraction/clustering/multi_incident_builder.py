"""
Multi-Incident Builder
======================
Takes a raw document, splits it into sentences, extracts features per sentence,
filters through the Event Detector, clusters event-bearing sentences,
builds incidents, and deduplicates the results.

Pipeline:
    Document
        ↓
    Sentence Splitting
        ↓
    Feature Extraction (per sentence)
        ↓
    Event Detection (filter administrative content)
        ↓
    Boundary-Aware Context Propagation
        ↓
    Clustering (event sentences only)
        ↓
    Incident Construction
        ↓
    Incident Deduplication
        ↓
    Final Incidents
"""

import uuid
import spacy
from typing import List

from models.document import Document
from models.incident import Incident, generate_retrieval_text

from extraction.date_extractor import extract_date
from extraction.location_extractor import extract_location
from extraction.casualty_extractor import extract_casualties
from extraction.organization_extractor import extract_organizations
from extraction.attack_extractor import (
    extract_attack_types,
    extract_weapon_types,
    extract_target_types,
)
from extraction.event_detector import detect_event
from extraction.incident_deduplicator import deduplicate_incidents

from .models import SentenceEvent, EventCluster
from .anchor_detector import is_anchor_sentence, has_narrative_boundary
from .event_clusterer import cluster_events

# Load English tokenizer, tagger, parser and NER
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if model not installed
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")



def build_multi_incidents(document: Document) -> List[Incident]:
    """
    Extracts 0 to N Incidents from a single Document.
    """
    text = document.raw_text
    
    # 1. Sentence Splitting
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    
    raw_events: List[SentenceEvent] = []
    
    # PASS 1: Strictly Sentence-Scoped Extraction
    for i, sent_text in enumerate(sentences):
        date = extract_date(sent_text)
        location = extract_location(sent_text)
        casualties = extract_casualties(sent_text)
        organizations = extract_organizations(sent_text)
        
        event = SentenceEvent(
            sentence_id=i,
            text=sent_text,
            date=date,
            country=location["country"],
            state=location["state"],
            city=location["city"],
            attack_types=extract_attack_types(sent_text),
            weapon_types=extract_weapon_types(sent_text),
            target_organizations=organizations["target_organizations"],
            responsible_groups=organizations["responsible_groups"],
            killed=casualties["killed"],
            injured=casualties["injured"],
            is_anchor=is_anchor_sentence(sent_text)
        )
        raw_events.append(event)
        
    # PASS 1.5: Event Detection — classify each sentence
    for event in raw_events:
        detection = detect_event(event.text)
        event.event_classification = detection.classification
        event.event_score = detection.event_score
        event.admin_score = detection.admin_score
        
    # PASS 2: Boundary-Aware Context Window for Dates and Locations
    # We look at idx-1 and idx+1. If we lack a date/location, we can borrow it
    # IF there is no boundary between us and the neighbor.
    def _is_boundary(e1: SentenceEvent, e2: SentenceEvent) -> bool:
        """Returns True if there is a hard boundary between e1 and e2."""
        if has_narrative_boundary(e1.text) or has_narrative_boundary(e2.text):
            return True
        if e1.is_anchor and e2.is_anchor:
            return True # Two distinct anchors imply a boundary
        # Explicit date mismatch
        if e1.date and e2.date and e1.date != e2.date:
            return True
        # Explicit location mismatch
        if e1.city and e2.city and e1.city != e2.city:
            return True
        # Event classification boundary: don't borrow across REJECT boundaries
        if e1.event_classification == "REJECT" or e2.event_classification == "REJECT":
            return True
        return False

    for i in range(len(raw_events)):
        curr = raw_events[i]
        
        # Try to fill Date
        if not curr.date:
            if i > 0 and raw_events[i-1].date and not _is_boundary(raw_events[i-1], curr):
                curr.date = raw_events[i-1].date
            elif i < len(raw_events)-1 and raw_events[i+1].date and not _is_boundary(curr, raw_events[i+1]):
                curr.date = raw_events[i+1].date
                
        # Try to fill Location
        if not curr.city:
            if i > 0 and raw_events[i-1].city and not _is_boundary(raw_events[i-1], curr):
                curr.city = raw_events[i-1].city
                curr.state = raw_events[i-1].state
                curr.country = raw_events[i-1].country
            elif i < len(raw_events)-1 and raw_events[i+1].city and not _is_boundary(curr, raw_events[i+1]):
                curr.city = raw_events[i+1].city
                curr.state = raw_events[i+1].state
                curr.country = raw_events[i+1].country
                
    # 3. Clustering (Event Detector classification is respected inside cluster_events)
    clusters = cluster_events(raw_events)
    
    incidents: List[Incident] = []
    
    # 4. Incident Construction
    for cluster in clusters:
        all_sents = cluster.all_sentences
        
        # Merge Sets
        attack_types = set()
        weapon_types = set()
        target_orgs = set()
        resp_groups = set()
        
        # Track most specific location and date
        merged_date = None
        merged_country = None
        merged_state = None
        merged_city = None
        
        # Max casualties
        total_killed = 0
        total_injured = 0
        
        summary_sentences = []
        
        # Sort by sentence ID to rebuild summary in order
        all_sents.sort(key=lambda s: s.sentence_id)
        
        for s in all_sents:
            summary_sentences.append(s.text)
            
            if s.date and not merged_date: merged_date = s.date
            if s.country and not merged_country: merged_country = s.country
            if s.state and not merged_state: merged_state = s.state
            if s.city and not merged_city: merged_city = s.city
            
            attack_types.update(s.attack_types)
            weapon_types.update(s.weapon_types)
            target_orgs.update(s.target_organizations)
            resp_groups.update(s.responsible_groups)
            
            # Use max casualties across the cluster to avoid double-counting
            # ("5 killed in blast. The 5 victims were...")
            if s.killed > total_killed: total_killed = s.killed
            if s.injured > total_injured: total_injured = s.injured
            
        summary = " ".join(summary_sentences)
        
        # Build Final Incident
        incident = Incident(
            incident_id=str(uuid.uuid4()),
            date=merged_date,
            country=merged_country,
            state=merged_state,
            city=merged_city,
            location_confidence=1.0 if merged_city else 0.5, # simplified
            attack_types=list(attack_types),
            target_types=[], # Note: target_types should also be merged
            weapon_types=list(weapon_types),
            responsible_groups=list(resp_groups),
            target_organizations=list(target_orgs),
            killed=total_killed,
            injured=total_injured,
            summary=summary,
            source_document_id=document.doc_id
        )
        
        # Also collect target types (the general ones like "Military", "Civilian")
        tgt_types = set()
        for s in all_sents:
            tgt_types.update(extract_target_types(s.text))
        incident.target_types = list(tgt_types)
        
        incident.has_summary = True
        incident.retrieval_text = generate_retrieval_text(incident)
        
        incidents.append(incident)
    
    # 4.5 Document-Level Entity Enrichment
    # Responsible groups and target organizations are often mentioned in
    # administrative/context sentences (e.g. charge-sheet paragraphs) that
    # the Event Detector correctly classifies as REJECT. We extract these
    # entities from the FULL document text and enrich incidents that are
    # missing this information.
    if incidents:
        doc_orgs = extract_organizations(document.raw_text)
        doc_resp_groups = doc_orgs["responsible_groups"]
        doc_target_orgs = doc_orgs["target_organizations"]
        
        for incident in incidents:
            # Enrich responsible groups if missing
            if not incident.responsible_groups and doc_resp_groups:
                incident.responsible_groups = doc_resp_groups
            
            # Enrich target organizations if missing
            if not incident.target_organizations and doc_target_orgs:
                incident.target_organizations = doc_target_orgs
            
            # Regenerate retrieval text after enrichment
            incident.retrieval_text = generate_retrieval_text(incident)
    
    # 5. Incident Deduplication
    incidents = deduplicate_incidents(incidents)
        
    return incidents
