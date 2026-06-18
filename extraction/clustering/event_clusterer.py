"""
Event Clusterer
===============
Agglomerative clustering of SentenceEvents based on weighted similarity.
"""

from typing import List
from .models import SentenceEvent, EventCluster

CLUSTER_THRESHOLD = 0.5

# Weights
W_LOC = 0.35
W_DATE = 0.25
W_ACTOR = 0.20
W_ATTACK = 0.10
W_PROX = 0.10

def _location_similarity(s1: SentenceEvent, s2: SentenceEvent) -> float:
    # Exact city match
    if s1.city and s2.city:
        if s1.city == s2.city: return 1.0
        return -0.5 # Penalty for explicit mismatch
    
    # State match
    if s1.state and s2.state:
        if s1.state == s2.state: return 0.8
        return -0.2
        
    # Country match
    if s1.country and s2.country:
        if s1.country == s2.country: return 0.5
        
    return 0.0

def _date_similarity(s1: SentenceEvent, s2: SentenceEvent) -> float:
    if s1.date and s2.date:
        if s1.date == s2.date:
            return 1.0
        return -0.5 # Explicit mismatch
    return 0.0

def _actor_similarity(s1: SentenceEvent, s2: SentenceEvent) -> float:
    score = 0.0
    
    s1_resp = set(s1.responsible_groups)
    s2_resp = set(s2.responsible_groups)
    if s1_resp and s2_resp:
        if s1_resp.intersection(s2_resp):
            score += 0.5
            
    s1_targ = set(s1.target_organizations)
    s2_targ = set(s2.target_organizations)
    if s1_targ and s2_targ:
        if s1_targ.intersection(s2_targ):
            score += 0.5
            
    # If no groups extracted in one sentence, we don't penalize, just neutral
    return score

def _attack_similarity(s1: SentenceEvent, s2: SentenceEvent) -> float:
    score = 0.0
    s1_atk = set(s1.attack_types)
    s2_atk = set(s2.attack_types)
    if s1_atk and s2_atk and s1_atk.intersection(s2_atk):
        score += 0.5
        
    s1_weap = set(s1.weapon_types)
    s2_weap = set(s2.weapon_types)
    if s1_weap and s2_weap and s1_weap.intersection(s2_weap):
        score += 0.5
        
    return score

def _proximity_similarity(s1: SentenceEvent, cluster_sentences: List[SentenceEvent]) -> float:
    # Find the shortest distance to any sentence already in the cluster
    min_diff = min(abs(s1.sentence_id - s2.sentence_id) for s2 in cluster_sentences)
    if min_diff == 1:
        return 1.0
    elif min_diff == 2:
        return 0.5
    elif min_diff <= 4:
        return 0.2
    return 0.0

from .anchor_detector import has_narrative_boundary, ATTACK_ANCHORS, OPERATION_ANCHORS
import re

def _contains_any(text: str, keywords: list) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            return True
    return False

def calculate_boundary_score(s1: SentenceEvent, cluster: EventCluster) -> float:
    """
    Calculates a boundary score representing evidence that s1 and the cluster
    belong to DIFFERENT incidents.
    """
    score = 0.0
    anchor = cluster.anchor_sentence
    
    # 1. Narrative Transitions
    if has_narrative_boundary(s1.text):
        score += 1.0
        
    # 2. Date Mismatch
    if s1.date and anchor.date and s1.date != anchor.date:
        score += 1.0
        
    # 3. Location Mismatch
    if s1.city and anchor.city and s1.city != anchor.city:
        score += 1.0
        
    # 4. Attack Type Mismatch (e.g. Bombing vs Encounter)
    s1_is_op = _contains_any(s1.text, OPERATION_ANCHORS)
    s1_is_atk = _contains_any(s1.text, ATTACK_ANCHORS)
    anchor_is_op = _contains_any(anchor.text, OPERATION_ANCHORS)
    anchor_is_atk = _contains_any(anchor.text, ATTACK_ANCHORS)
    
    if (s1_is_op and not s1_is_atk) and (anchor_is_atk and not anchor_is_op):
        score += 1.0
    elif (s1_is_atk and not s1_is_op) and (anchor_is_op and not anchor_is_atk):
        score += 1.0
        
    # 5. GTD Attack Type Mismatch
    if s1.attack_types and anchor.attack_types:
        if not set(s1.attack_types).intersection(set(anchor.attack_types)):
            score += 0.5
            
    # 6. Responsible Group Mismatch
    if s1.responsible_groups and anchor.responsible_groups:
        if not set(s1.responsible_groups).intersection(set(anchor.responsible_groups)):
            score += 0.5
            
    return score

def calculate_similarity(s1: SentenceEvent, cluster: EventCluster) -> float:
    """Calculates weighted similarity between a SentenceEvent and an EventCluster."""
    
    # If boundary evidence is too strong, force split
    boundary_score = calculate_boundary_score(s1, cluster)
    if boundary_score >= 1.0:
        return -1.0
        
    anchor = cluster.anchor_sentence
    
    # We compare metadata against the anchor for stability
    loc_sim = _location_similarity(s1, anchor)
    date_sim = _date_similarity(s1, anchor)
    actor_sim = _actor_similarity(s1, anchor)
    atk_sim = _attack_similarity(s1, anchor)
    
    # But proximity is compared against the whole cluster to form contiguous blocks
    prox_sim = _proximity_similarity(s1, cluster.all_sentences)
    
    score = (W_LOC * loc_sim) + (W_DATE * date_sim) + (W_ACTOR * actor_sim) + \
            (W_ATTACK * atk_sim) + (W_PROX * prox_sim)
            
    # Context carry-over heuristic:
    # If sentences are adjacent (prox_sim == 1.0) and there are NO contradictions,
    # it is highly likely they are part of the same narrative block.
    if prox_sim == 1.0 and score < CLUSTER_THRESHOLD:
        score = CLUSTER_THRESHOLD
        
    return score

def cluster_events(sentences: List[SentenceEvent], threshold: float = CLUSTER_THRESHOLD) -> List[EventCluster]:
    """
    Groups SentenceEvents into Incident Clusters.
    """
    clusters: List[EventCluster] = []
    cluster_counter = 0
    
    for sent in sentences:
        best_score = -1.0
        best_cluster = None
        
        # Compare sentence to all existing clusters
        for cluster in clusters:
            score = calculate_similarity(sent, cluster)
            if score > best_score:
                best_score = score
                best_cluster = cluster
                
        # If it's a strong match, add to existing cluster regardless of whether it's an anchor
        if best_cluster and best_score >= threshold:
            sent.cluster_id = best_cluster.cluster_id
            best_cluster.supporting_sentences.append(sent)
        else:
            # If no strong match, and it's an anchor (or has enough entities to be promoted), create a new cluster
            if sent.is_anchor or sent.attack_types or sent.weapon_types or sent.killed > 0 or sent.injured > 0:
                cluster_counter += 1
                sent.is_anchor = True # promote
                sent.cluster_id = cluster_counter
                new_cluster = EventCluster(cluster_id=cluster_counter, anchor_sentence=sent)
                clusters.append(new_cluster)

    return clusters
